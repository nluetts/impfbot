import sys
import argparse
from log import log
import settings
import alerts

import api_wrapper

from common import sleep, sleep_until, is_night, datetime2timestamp


def check_for_slot() -> None:
    try:
        birthdate_timestamp = datetime2timestamp(settings.BIRTHDATE)
        result = api_wrapper.fetch_api(
            plz=settings.ZIP,
            birthdate_timestamp=birthdate_timestamp,
            max_retries=10,
            sleep_after_error=settings.COOLDOWN_BETWEEN_FAILED_REQUESTS_IN_S,
            sleep_after_shadowban=settings.COOLDOWN_AFTER_DETECTED_SHADOWBAN_IN_S,
            user_agent=settings.USER_AGENT)

        if not result:
            log.error("Result is emtpy. (Invalid ZIP Code (PLZ)?)")
        for elem in result:
            if not elem['outOfStock']:
                free_slots = elem['freeSlotSizeOnline']
                vaccine_name = elem['vaccineName']
                vaccine_type = elem['vaccineType']
                log.info(
                    f"Free slot! (%s) {vaccine_name}/{vaccine_type}")

                msg = f"Freier Impfslot ({free_slots})! {vaccine_name}/{vaccine_type}"

                alerts.alert(msg)

                sleep(settings.COOLDOWN_AFTER_SUCCESS_IN_S, 0)
            else:
                log.info("No free slot.")
    except Exception as e:
        log.error(f"Something went wrong ({e})")


if __name__ == "__main__":
    try:
        parser = argparse.ArgumentParser(
            description='Notification bot for the lower saxony vaccination portal ')
        parser.add_argument('-f', '-c', '--config',
                            dest='configfile',
                            help='Path to config.ini file',
                            required=False,
                            default='config.ini')
        arg = vars(parser.parse_args())

        try:
            settings.load(arg['configfile'])
        except (settings.ParseExeption, FileNotFoundError) as e:
            log.error(e)
            sys.exit(1)
        except Exception as e:
            log.warning(e)

        while True:
            if is_night() and settings.SLEEP_AT_NIGHT:
                log.info("It's night. Sleeping until 7am")
                sleep_until(hour=7, minute=0)

            check_for_slot()
            sleep(settings.COOLDOWN_BETWEEN_REQUESTS_IN_S, settings.JITTER)

    except (KeyboardInterrupt, SystemExit):
        print("Bye...")
