from google.appengine.api import users, mail
from google.appengine.ext import db
from datetime import timedelta, datetime
import webapp2,cgi,jinja2,os,random

JINJA_ENVIRONMENT = jinja2.Environment(
loader = jinja2.FileSystemLoader(os.path.dirname(__file__)),
extensions=['jinja2.ext.autoescape'],
autoescape=True)

ADD_POINT_RECYCLING = 4; #Point increment recycling
ADD_POINT_TRASH = 1; #Point increment trash
SPECIAL_KEY_RECYCLING = '71417320de826ebc9688de68c8232383' #URL variable for recycling bin QR
SPECIAL_KEY_TRASH =     '0d16f5ce62a2d8e62a282409abd95503' #URL variable for trash bin QR 

class Player(db.Model):
	name = db.StringProperty()
	points = db.IntegerProperty()
	updateTime = db.DateTimeProperty()

class LeadersPage(webapp2.RequestHandler):

	def get(self):
		topPlayers = db.GqlQuery("SELECT * FROM Player WHERE points>0 ORDER BY points DESC")
		leaderboard_template_values = {
		'topplayers':topPlayers
		}
		leaderboard_template = JINJA_ENVIRONMENT.get_template('templates/leaderboard.html')
		self.response.write(leaderboard_template.render(leaderboard_template_values))		

class AddPoint(webapp2.RequestHandler):

	def get(self):
		IS_VALID = False
		if(self.request.get('special')):
			special = str(self.request.get('special'))
			if(special==SPECIAL_KEY_RECYCLING or special==SPECIAL_KEY_TRASH):
				if special==SPECIAL_KEY_RECYCLING:
					ADD_POINT = ADD_POINT_RECYCLING
				else:
					ADD_POINT = ADD_POINT_TRASH
				user = users.get_current_user()
				if user:
					allUsers = matchingUsersFor(user)
					print len(allUsers)
					if len(allUsers) == 0:
						print "[D]-New User"
						player = Player(name=user.email(),points=ADD_POINT)
						IS_VALID = True
					else:
						print "[D]-Updated User"
						player = allUsers[0]
						player.points += ADD_POINT
						if(player.updateTime):
							oldUpdate = player.updateTime
							timeDifference = datetime.now() - oldUpdate
							if(ADD_POINT==SPECIAL_KEY_RECYCLING):
								checkTime = random.randint(1800,3600)
							else:
								checkTime = random.randint(300,600)
							if timeDifference.seconds > checkTime:
								IS_VALID = True
						else:
							IS_VALID = True
					if(IS_VALID):
						player.updateTime = datetime.now()
						player.put()
						point_template_values = {
						'amount':ADD_POINT
						}
						point_template = JINJA_ENVIRONMENT.get_template('templates/point.html')
						self.response.write(point_template.render(point_template_values))
					else:
						error_template = JINJA_ENVIRONMENT.get_template('templates/error.html')
						self.response.write(error_template.render())						
				else:
					self.redirect(users.create_login_url(self.request.uri))
			else:
				self.redirect('/')
		else:
			self.redirect('/')


class UserProfile(webapp2.RequestHandler):

	def get(self):
		currentUser = users.get_current_user()
		if currentUser:
			players = matchingUsersFor(currentUser)
			if(len(players)==1):
				player = players[0]
			else:
				player = Player(name=currentUser.email(),points=0,nickname=currentUser.nickname())
				player.put()			
			user_template_values = {
				'username':player.name,
				'points':player.points,
				'logout_url': users.create_logout_url("/"),
				'level': getLevel(player.points)
				}		
			user_template = JINJA_ENVIRONMENT.get_template('templates/user.html')
			self.response.write(user_template.render(user_template_values))	

		else:
			self.redirect(users.create_login_url(self.request.url))

class PurgeMain(webapp2.RequestHandler):

	def get(self):
		emailWinner()
		playerKeys = Player.all(keys_only=True)
		for key in playerKeys:
			db.delete(key)

def emailWinner():
	
	maxPoints = None
	try: 
		maxPoints = Player.all().order('-points').get().points
	except AttributeError:
		print "[D]-No Users..."
	if maxPoints is not None:
		winners = db.GqlQuery("SELECT * FROM Player WHERE points=:1",maxPoints)
		for winner in winners:
			winnerEmail = winner.name
			message  = mail.EmailMessage(sender="Recycled Admin <dev.tahoma@mysummitps.org>", subject="You've won Recycled!")
			message.to = winnerEmail
			message.body="""
			Congratulations %s for winning this month's Recycled! \n 
			Please contact anguyen.sj@mysummitps.org or aramesh.sj@mysummitps.org to redeem your prize. 

			---- 
			This was an automated message sent by Lamar the bot. Do not reply to this email.
			(Service still in beta)
			""" % winnerEmail
			message.send()
				


def getLevel(points):

	if 4<=points<=10:
		return 'Novice Sanitarian'
	elif 11<=points<=15:
		return 'Regular Sanitarian'
	elif 16<=points<=20:
		return 'Master Sanitarian'
	elif 21<=points<=25:
		return 'Novice Trashmaster'
	elif 26<=points<=30:
		return 'Regular Trashmaster'
	elif 31<=points<=35:
		return 'Master Trashmaster'
	elif points>=36:
		return 'Emperor Rubbish'



def matchingUsersFor(user):
	return db.GqlQuery("SELECT * FROM Player WHERE name=:1",user.email()).fetch(1)


def emailUser(user,message):
	print("User: "+user)
	print("Message: "+message)



application = webapp2.WSGIApplication({
	('/',LeadersPage),
	('/point',AddPoint),
	('/user',UserProfile),
	('/purgemain',PurgeMain)
},debug=True)