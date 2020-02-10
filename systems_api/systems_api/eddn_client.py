import zlib
import transaction
import zmq
import simplejson
import sys
import time
import os

from xmlrpc.client import ServerProxy

from pyramid.paster import (
    get_appsettings,
    setup_logging,
    )

from pyramid.scripts.common import parse_vars
from sqlalchemy import func

from systems_api.models import (
    get_engine,
    get_session_factory,
    get_tm_session,
    )


from systems_api.models.star import Star
from systems_api.models.system import System

__relayEDDN = 'tcp://eddn.edcd.io:9500'
__timeoutEDDN = 600000

__scoopable = ['K', 'G', 'B', 'F', 'O', 'A', 'M']


def usage(argv):
    cmd = os.path.basename(argv[0])
    print('usage: %s <config_uri> [var=value]\n'
          '(example: "%s development.ini")' % (cmd, cmd))
    sys.exit(1)


def main(argv=sys.argv):
    if len(argv) < 2:
        usage(argv)
    config_uri = argv[1]
    options = parse_vars(argv[2:])
    setup_logging(config_uri)
    settings = get_appsettings(config_uri, options=options)
    serverurl = settings['xml_proxy']
    proxy = ServerProxy(serverurl)
    engine = get_engine(settings)
    session_factory = get_session_factory(engine)
    session = get_tm_session(session_factory, transaction.manager)

    context = zmq.Context()
    subscriber = context.socket(zmq.SUB)

    subscriber.setsockopt(zmq.SUBSCRIBE, b"")
    subscriber.setsockopt(zmq.RCVTIMEO, __timeoutEDDN)
    starttime = time.time()
    messages = 0
    updated = 0
    syscount = 0
    starcount = 0

    while True:
        try:
            subscriber.connect(__relayEDDN)

            while True:
                __message = subscriber.recv()

                if not __message:
                    subscriber.disconnect(__relayEDDN)
                    break

                __message = zlib.decompress(__message)
                __json = simplejson.loads(__message)
                if time.time() > (starttime + 3600):
                    try:
                        startot = session.query(func.count(Star.id64)).scalar()
                        systot = session.query(func.count(System.id64)).scalar()
                        proxy.command("botserv", "Absolver", f"say #announcerdev [SAPI]: {messages} msgs processed"
                                                             f", {syscount} new systems, {starcount} new stars."
                                                             f" DB contains {startot} stars and {systot} systems.")
                        messages = 0
                        syscount = 0
                        starcount = 0
                        starttime = time.time()
                    except TimeoutError:
                        print("XMLRPC call failed due to timeout, retrying in 60 seconds.")
                        starttime = starttime + 60
                data = __json['message']
                messages = messages + 1
                if 'event' in data:
                    if data['event'] == 'FSDJump':
                        id64 = data['SystemAddress']
                        res = session.query(System).filter(System.id64 == id64).count()
                        print(f"Row count: {res}")
                        if res == 0:
                            syscount = syscount + 1
                            print("Adding new row...")
                            newsys = System(id64=data['SystemAddress'], name=data['StarSystem'],
                                            coords=data['StarPos'], date=data['timestamp'])
                            session.add(newsys)
                            transaction.commit()
                    if data['event'] == 'Scan':
                        bodyid = data['SystemAddress'] + (data['BodyID'] << 55)
                        if 'AbsoluteMagnitude' in data:
                            # It's a star!
                            res = session.query(Star).filter(Star.id64 == bodyid).count()
                            starcount = starcount + 1
                            if res == 0:
                                # print(f"Stardata: {data}")
                                newstar = Star(id64=bodyid, bodyId=data['BodyID'], name=data['BodyName'],
                                               age=data['Age_MY'], axialTilt=data['AxialTilt'],
                                               orbitalEccentricity=data['Eccentricity']
                                               if 'Eccentricity' in data else None,
                                               orbitalInclination=data['OrbitalInclination']
                                               if 'OrbitalInclination' in data else None,
                                               orbitalPeriod=data['OrbitalPeriod']
                                               if 'OrbitalPeriod' in data else None,
                                               parents=data['Parents']
                                               if 'Parents' in data else None,
                                               argOfPeriapsis=data['Periapsis']
                                               if 'Periapsis' in data else None,
                                               belts=data['Rings'] if 'Rings' in data else None,
                                               semiMajorAxis=data['SemiMajorAxis']
                                               if 'SemiMajorAxis' in data else None,
                                               systemName=data['StarSystem'],
                                               distanceToArrival=data['DistanceFromArrivalLS'],
                                               luminosity=data['Luminosity'], solarRadius=data['Radius'],
                                               rotationalPeriod=data['RotationPeriod'], type=data['StarType'],
                                               solarMasses=data['StellarMass'],
                                               subType=data['Subclass'] if 'Subclass' in data else None,
                                               surfaceTemperature=data['SurfaceTemperature'],
                                               isScoopable=True if data['StarType'] in __scoopable else False,
                                               isMainStar=True if data['BodyID'] == 1 else False,
                                               updateTime=data['timestamp'])
                                session.add(newstar)
                                print("Added new star.")
                                transaction.commit()
                sys.stdout.flush()

        except zmq.ZMQError as e:
            print('ZMQSocketException: ' + str(e))
            sys.stdout.flush()
            subscriber.disconnect(__relayEDDN)
            time.sleep(5)


if __name__ == '__main__':
    main()
