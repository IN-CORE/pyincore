# Copyright (c) 2019 University of Illinois and others. All rights reserved.
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/
import requests
from pyincore import globals as pyglobals

logger = pyglobals.LOGGER


def return_http_response(http_response):
    try:
        http_response.raise_for_status()
        return http_response
    except requests.exceptions.HTTPError:
        logger.error(
            "A HTTPError has occurred \n"
            + "HTTP Status code: "
            + str(http_response.status_code)
            + "\n"
            + "Error Message: "
            + http_response.content.decode()
        )
        raise
    except requests.exceptions.ConnectionError:
        logger.error(
            "ConnectionError: Failed to establish a connection with the server. "
            "This might be due to a refused connection. "
            "Please check that you are using the right URLs."
        )
        raise
    except requests.exceptions.RequestException:
        logger.error(
            "RequestException: There was an exception while trying to handle your request. "
            "Please go to the end of this message for more specific information about the exception."
        )
        raise
