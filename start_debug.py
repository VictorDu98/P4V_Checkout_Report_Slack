import model

class Model_debug(model.Model):
    def __init__(self, name):
        super().__init__(name)
        self.webhook = "https://prod-93.southeastasia.logic.azure.com:443/workflows/7aaf012f794f47a4be63ff3e35fa9877/triggers/manual/paths/invoke?api-version=2016-06-01&sp=%2Ftriggers%2Fmanual%2Frun&sv=1.0&sig=8yHEY2BHprJlXKYQKCsI92qXucAa7BkgaLTzX7POYSc"


def main(*args):
    #GFH = Model_debug("GFH")
    #GFH.run()
    #ISN_ENV_1 = Model_debug("ISN_ENV_1")
    #ISN_ENV_1.run()
    ISN_ENV_2 = Model_debug("ISN_ENV_2")
    ISN_ENV_2.run()
    #ISN_VFX_1 = Model_debug("ISN_VFX_1")
    #ISN_VFX_1.run()
    #ISN_VFX_2 = Model_debug("ISN_VFX_2")
    #ISN_VFX_2.run()

main()