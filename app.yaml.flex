runtime: python
env: flex
entrypoint: gunicorn -c gunicornconf.py -b :8080 main:app

runtime_config:
  python_version: 3

# This sample incurs costs to run on the App Engine flexible environment. 
# The settings below are to reduce costs during testing and are not appropriate
# for production use. For more information, see:
# https://cloud.google.com/appengine/docs/flexible/python/configuring-your-app-with-app-yaml
manual_scaling:
  instances: 1
resources:
  cpu: 1
  memory_gb: 1
  disk_size_gb: 10
