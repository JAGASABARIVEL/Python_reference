from fabric import auth
from fabric.operations import env, settings
from fabric import operations


# Common Functions

accepted = ['Y', 'y', 'yes', 'YES', 'Yes']
rejected = ['N', 'n', 'no', 'NO', 'No']


class StaticLibrary:
    def __init__(self):
	pass
    def set_class_variable(self, prompt):
        self.prompt = prompt

    def get_class_variable(self):
        return self.prompt

    def default_confirmation_y(self, input):
        if bool(input) is False:
            return 'Y'
        elif bool(input) is True:
            return input

    def default_confirmation_n(self, input):
        if bool(input) is False:
            return 'N'
        elif bool(input) is True:
            return input

    def user_interface(self, mandatory_param=False):
        if mandatory_param:
            receive = raw_input(self.prompt)
            if bool(receive) is False:
                return "[ERROR] Provide an rpm path."
            else:
                return receive
        else:
            receive = raw_input(self.prompt)
            return receive


class StaticFabric(object):
    def __init__(self):
        pass

    def set_host(self, host):
        env.host_string = host

    def set_authentication(self, user, host, port, password):
        auth.set_password(user, host, port, password)

    def local(self, cmd):
        with settings(warn_only=True):
            return operations.local(cmd)

    def remote(self, cmd):
        with settings(warn_only=True):
            return operations.run(cmd)

    def parse(style=None):
        pass


if __name__ == "__main__":

    #################################################
    #   1. Confirmation for taking the services down.
    #################################################

    
    prompt = "All the pps related services will be taken down.Please confirm for processing further [%s]|%s\t: " % (
        'Y', 'N')
    common = StaticLibrary()
    common.set_class_variable(prompt)
    receive = common.user_interface()

    print "Here 3"
    service_down_confirmation = common.default_confirmation_y(receive)
    del common

    #############################################
    # 2. Get the path of the rpm to be installed.
    #############################################
    prompt = "Please enter the path of the rpm to be installed : "
    common = StaticLibrary()
    common.set_class_variable(prompt)
    receive = common.user_interface()
    del common

    ######################### PRE DEPLOYMENT ####################

    #############################################################
    # 3. Check for the log space and get confirmation to cleanup.
    #############################################################

    ######################################################
    # 4. Down the services based on the user confirmation.
    ######################################################
    if service_down_confirmation in accepted:
        action = StaticFabric()
        action.set_host("10.78.217.21")
        action.set_authentication("root", "10.78.217.21", "22", "master1")
        action.remote("service nds_pps status")
        del action
        print "[SUCCESS] Made the pps related services down."
    ###########################################################
    # 5. Collect and back up the existing configuration folder.
    ###########################################################
    action = StaticFabric()
    action.set_host("10.78.217.21")
    action.set_authentication("root", "10.78.217.21", "22", "master1")
    action.remote('rm -r /tmp/.pps_upgrade')
    action.remote('mkdir -p /tmp/.pps_upgrade/etc')
    action.remote('cp -r /opt/nds/pps/etc /tmp/.pps_upgrade/etc')
    print "[SUCCESS] Backed up the existing configuration."
    del action

    ############################### DEPLOYMENT PHASE #########################

    ##################################
    # 1. unlink the current pps build.
    ##################################

    action = StaticFabric()
    action.set_host("10.78.217.21")
    action.set_authentication("root", "10.78.217.21", "22", "master1")
    action.remote("unlink /tmp/Jaga")
    del action
    print "[SUCCESS] Unlinked the existing pps build."

    #################################
    # 2. soft link the new pps build.
    #################################
    action = StaticFabric()
    action.set_host("10.78.217.21")
    action.set_authentication("root", "10.78.217.21", "22", "master1")
    action.remote("ln -s %s /tmp/Jaga" % ('/var/log'))
    del action
    print "[SUCCESS] Linked the new pps build."

    ############################
    # 3. Set the configurations.
    ############################
    action = StaticFabric()
    action.set_host("10.78.217.21")
    action.set_authentication("root", "10.78.217.21", "22", "master1")
    action.remote("cp -r /tmp/.pps_upgrade/etc/* /tmp/Jaga/etc/.")
    del action
    print "[SUCCESS] Copied the older configuration to the new build."

    ############################### POST DEPLOYMENT PHASE ####################

    ######################################
    # 1. Start all the concerned services.
    ######################################
    action = StaticFabric()
    action.set_host("10.78.217.21")
    action.set_authentication("root", "10.78.217.21", "22", "master1")
    action.remote("servive nds_pps start")
    del action
    print "[SUCCESS] Restarted the pps related services."

    ##########################
    # 2. Querry the ensure.js.
    ##########################

    ########################################################
    # 3. Ensure mogo service is running and webserver is up.
    ########################################################
