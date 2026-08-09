// Portable Remotion config for the automontage pipeline.
//
// Environments differ in whether Remotion may download its own Chrome Headless
// Shell. Sandboxes and CI images often block that download but ship a Chromium
// build already. Both knobs below are therefore environment-driven rather than
// hardcoded, so the same checkout works on a laptop and in a locked-down box:
//
//   REMOTION_BROWSER_EXECUTABLE  path to an existing Chrome/Chromium binary.
//                                Unset => Remotion downloads its own as usual.
//   REMOTION_IGNORE_CERT_ERRORS  set to "1" behind a TLS-intercepting proxy
//                                whose CA the browser does not trust.
import { Config } from "@remotion/cli/config";

const browserExecutable = process.env.REMOTION_BROWSER_EXECUTABLE;
if (browserExecutable) {
  Config.setBrowserExecutable(browserExecutable);
}

if (process.env.REMOTION_IGNORE_CERT_ERRORS === "1") {
  Config.setChromiumIgnoreCertificateErrors(true);
}
