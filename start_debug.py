from src import model


class Model_debug(model.Model):
    def __init__(self, name):
        super().__init__(name)
        self.webhook = "https://default2ca815949a7142a0a4870fc9de27d8.34.environment.api.powerplatform.com:443/powerautomate/automations/direct/workflows/7aaf012f794f47a4be63ff3e35fa9877/triggers/manual/paths/invoke?api-version=1&sp=%2Ftriggers%2Fmanual%2Frun&sv=1.0&sig=1Z6wz62e7Drg3vHGS16NNuWwddp6Z4GqOs_arJzE4WU"


def main(*args):
    #ISN_ENV_2 = Model_debug("ISN_ENV_2")
    #ISN_ENV_2.run()
    #ISN_VFX_2 = Model_debug("ISN_VFX_2")
    #ISN_VFX_2.run()
    RPT = Model_debug("RPT")
    RPT.run()
    #TEST_PROJECT =Model_debug("TEST_PROJECT")
    #TEST_PROJECT.run()

main()