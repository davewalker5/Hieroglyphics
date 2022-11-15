import sys
from hieroglyphics.web import create_app

environment = sys.argv[1] if len(sys.argv) > 1 else "development"
if environment == "development":
    create_app().run(debug=True, use_reloader=True)
else:
    create_app().run(host="0.0.0.0")
