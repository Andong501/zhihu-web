from flask import jsonify

from . import api
from ..models import Activity

@api.route('/activity/<int:id>')
def get_activity(id):
	activity = Activity.query.get_or_404(id)
	return jsonify(activity.to_json())