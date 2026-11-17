# pushraker-kiln: Kiln OS loads this component from the plugin's
# moonraker/components and puts its python/ on sys.path; this file hands
# over to the pushraker package shipped there (tools/vendor.py).
#
# This file may be distributed under the terms of the GNU GPLv3 license.
from pushraker.component import load_component  # noqa: F401
