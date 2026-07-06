"""P2 verification gate for SPEC_paypal_payment.md — a headless, in-process PayPal sandbox round-trip.

Runs the server-side payment logic directly (no Pyro, no GUI): create a PayPal order, print the
approval URL, wait for you to approve it in the browser as the sandbox BUYER, then capture and show
the resulting Transaction row. Proves credentials + gateway + entity end-to-end before any UI exists.

Prerequisites:
  - ../spectracsPy-server-config/.env filled with real sandbox Client ID / Secret / business payee.
  - Outbound HTTPS to api-m.sandbox.paypal.com (local machine is fine).

Run (from the server repo, reusing the app venv — see the run recipe):
  cd spectracsPy-server
  PYTHONPATH=".:../spectracsPy:../spectracsPy-model:../spectracsPy-base" \
      ../spectracsPy/venv/bin/python verify_paypal_payment.py --username masterUser
"""
import argparse

from sciens.spectracs.logic.config.ServerConfig import ServerConfig
from sciens.spectracs.logic.payment.PaymentLogicModule import PaymentLogicModule
from sciens.spectracs.logic.persistence.database.user.PersistUserLogicModule import PersistUserLogicModule
from sciens.spectracs.logic.user.UserSeedLogicModule import UserSeedLogicModule


def main():
    parser = argparse.ArgumentParser(description="PayPal sandbox payment round-trip verifier")
    parser.add_argument("--username", default="masterUser", help="seeded user to charge (default masterUser)")
    args = parser.parse_args()

    print("config dir :", ServerConfig.configDir())
    print("PAYPAL_ENV :", ServerConfig.get("PAYPAL_ENV", "(unset)"))
    print("API base   :", ServerConfig.get("PAYPAL_API_BASE", "(default)"))
    print("client id  :", "SET" if ServerConfig.get("PAYPAL_CLIENT_ID") else "MISSING")
    print("client sec :", "SET" if ServerConfig.get("PAYPAL_CLIENT_SECRET") else "MISSING")
    print("payee      :", ServerConfig.get("PAYPAL_PAYEE_EMAIL") or ServerConfig.get("PAYPAL_PAYEE_MERCHANT_ID") or "MISSING")
    print()

    # Ensure the seeded users exist (idempotent — the server does this on start).
    UserSeedLogicModule().seed()
    appUser = PersistUserLogicModule().findUserByUsername(args.username)
    if appUser is None:
        print("No such user: %s. Seeded users include masterUser / pumpkinTestUser." % args.username)
        return
    userId = appUser.id
    print("charging user: %s (%s)" % (args.username, userId))

    logic = PaymentLogicModule()

    created = logic.createPayment(userId)
    print("\ncreatePayment ->", created)
    if not created.get("ok"):
        print("\nFAILED at createPayment. Check the .env credentials / payee.")
        return
    orderId = created["orderId"]

    print("\n" + "=" * 70)
    print("OPEN THIS URL IN A BROWSER AND APPROVE AS THE SANDBOX BUYER:")
    print("  ", created["approvalUrl"])
    print("=" * 70)
    input("\nPress ENTER after you have approved the payment in the browser... ")

    captured = logic.capturePayment(userId, orderId)
    print("\ncapturePayment ->", captured)

    print("\nlistTransactions:")
    for dto in logic.listTransactions(userId):
        print("  ", dto)

    if captured.get("status") == "CAPTURED":
        print("\nP2 GATE PASSED: a real sandbox payment was captured and recorded.")
    else:
        print("\nNot captured (status=%s). If 'not approved yet', approve then re-run capture."
              % captured.get("status"))


if __name__ == "__main__":
    main()
