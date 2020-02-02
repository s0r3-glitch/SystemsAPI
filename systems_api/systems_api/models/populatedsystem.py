from sqlalchemy import (
    Column,
    BigInteger,
    Text,
    DateTime,
    JSON
)

from .meta import Base


class PopulatedSystem(Base):
    __tablename__ = 'populated_systems'
    id64 = Column(BigInteger, doc="64-bit system ID", primary_key=True)
    name = Column(Text, doc="System name")
    coords = Column(JSON, doc="System coordinates, as a JSON blob with X,Y and Z coordinates as floats.")
    controllingFaction = Column(JSON, doc="Controlling faction, in a JSON blob")
    date = Column(DateTime, doc="DateTime of last update to this system")
    date.info.update({'pyramid_jsonapi': {'visible': False}})