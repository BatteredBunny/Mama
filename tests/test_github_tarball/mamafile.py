import os
import mama

class test(mama.BuildTarget):
    workspace = 'packages'

    def settings(self):
        if os.environ.get('MAMA_ENABLE_TARBALL', '1') != '0':
            self.enable_tarball()

    def build(self):
        self.nothing_to_build()

    def dependencies(self):
        self.add_git('ExampleRemote', 'https://github.com/BatteredBunny/MamaExampleRemote.git', git_tag='v2.0.0')
        self.add_git('ExampleRemote2', 'https://github.com/BatteredBunny/MamaExampleRemote.git', git_tag='993e326cf840bc2df9d67b14d6e2fe0d38736713')
        self.add_git('ExampleRemote3', 'https://github.com/BatteredBunny/MamaExampleRemote.git', git_branch='master')
