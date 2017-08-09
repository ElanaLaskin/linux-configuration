import sys
from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine

Base = declarative_base()

class User(Base):
    __tablename__ = 'app_user'

    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    email = Column(String(250), nullable=False)
    picture = Column(String(250))

#The class is the table.The class inherits properties from sqlalchemy with the 'Base object'.
class Restaurant(Base):
	#The following line names the table
	__tablename__  = 'restaurant'
	
	#Here we create columns, using arguments that we imported on the top.
	name = Column(String(80), nullable=False) #this means that a row can't be created without this information
	id = Column(Integer, primary_key=True)
	app_user_id = Column(Integer, ForeignKey('app_user.id'))
	app_user = relationship(User)
	
	@property
	def serialize(self):
		return {
		'name': self.name,
		'id': self.id
		}

class MenuItem(Base):
	__tablename__ = 'menu_item'
	
	name = Column(String(80), nullable=False)
	id = Column(Integer, primary_key=True)
	course = Column(String(250))
	description = Column(String(250))
	price = Column(String(8))
	restaurant_id = Column(Integer, ForeignKey('restaurant.id'))
	restaurant = relationship(Restaurant)
	app_user_id = Column(Integer, ForeignKey('app_user.id'))
	app_user = relationship(User)

	@property
	def serialize(self):
		# Returns object data in easily serializable format
		return {
		'name': self.name,
		'description': self.description,
		'id': self.id,
		'price': self.price,
		'course': self.course
		}

engine = create_engine('postgresql://catalog:zxcv@localhost/restaurantmenu')
Base.metadata.create_all(engine)
