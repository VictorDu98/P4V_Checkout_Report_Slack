import model

class Model_debug(model.Model):
    def __init__(self, name):
        super().__init__(name)
        self.slack_uri = "https://hooks.slack.com/services/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"


def main(*args):
    GFH = Model_debug("GFH")
    GFH.run()
    ISN_ENV_1 = Model_debug("ISN_ENV_1")
    ISN_ENV_1.run()
    ISN_ENV_2 = Model_debug("ISN_ENV_2")
    ISN_ENV_2.run()
    ISN_VFX_1 = Model_debug("ISN_VFX_1")
    ISN_VFX_1.run()
    ISN_VFX_2 = Model_debug("ISN_VFX_2")
    ISN_VFX_2.run()

main()