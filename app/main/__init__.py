from flask import Blueprint

main = Blueprint('main', __name__) #build blueprint

from . import views, errors #relate to blueprint