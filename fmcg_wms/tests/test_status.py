import unittest
from types import SimpleNamespace

from fmcg_wms.services.status import get_shipment_status


class TestShipmentStatus(unittest.TestCase):
    def test_dispatched_status(self):
        items = [SimpleNamespace(dispatched_qty=5, received_qty=0, returned_qty=0)]
        self.assertEqual(get_shipment_status(items), "Dispatched")

    def test_partial_receipt_status(self):
        items = [SimpleNamespace(dispatched_qty=5, received_qty=2, returned_qty=0)]
        self.assertEqual(get_shipment_status(items), "Partially Received")

    def test_received_status(self):
        items = [SimpleNamespace(dispatched_qty=5, received_qty=5, returned_qty=0)]
        self.assertEqual(get_shipment_status(items), "Received")

    def test_mixed_closed_status(self):
        items = [SimpleNamespace(dispatched_qty=5, received_qty=3, returned_qty=2)]
        self.assertEqual(get_shipment_status(items), "Closed")
