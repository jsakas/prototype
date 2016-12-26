import os, sys, shutil


class InitializeProject(object):
	def __init__(self, project_name):
		package_location = os.path.dirname(os.path.realpath(__file__))
		package_template_location = os.path.join(package_location, 'template')
		project_location = os.path.join(os.getcwd(), project_name)

		if os.path.exists(project_location):
			exit('Cannot create project "{}" - directory already exists.'.format(project_name))
			
		os.makedirs(project_location)

		try:
			for f in os.listdir(package_template_location):
				if os.path.isfile(os.path.join(package_template_location, f)):
					shutil.copyfile(os.path.join(package_template_location, f), os.path.join(project_location, f))
				else:
					shutil.copytree(os.path.join(package_template_location, f), os.path.join(project_location, f))
		except Exception as e:
			print(e)

		print('Creating new Prototype project "{}" ... done.'.format(project_name))
		return
