PostgreSQL plugin for `Tutor <https://docs.tutor.edly.io>`__
############################################################

This plugin provides a PostgreSQL database backend for Tutor.


Installation
************

.. code-block:: bash

    pip install git+https://github.com/qasimgulzar/tutor-contrib-postgresql

Usage
*****

First, enable the plugin itself

.. code-block:: bash

    tutor plugins enable postgresql

Then, we need to build the openedx to bind the necessary postgresql packages and libraries into the image

.. code-block:: bash

    tutor images build openedx

Finally, launch the platform to initialize the database with the services.

.. code-block:: bash

    tutor local launch


License
*******

This software is licensed under the terms of the AGPLv3.
