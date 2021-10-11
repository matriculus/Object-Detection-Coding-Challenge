import unittest
import utils
import numpy as np

class PerceptionTest(unittest.TestCase):

    def test_shortDistanceToBox(self):
        # Distance from the point to the box
        bbox = np.array([[0,0], [1,0], [1,1], [0,1], [0, 0]])
        point = np.array([0.5, 0.5])
        d = utils.shortDistanceToBox(bbox, point)
        self.assertTrue(d, 0.5)

        point = np.array([0.5, 0])
        d = utils.shortDistanceToBox(bbox, point)
        self.assertLess(d, np.finfo(float).tiny)

        point = np.array([0, 0.5])
        d = utils.shortDistanceToBox(bbox, point)
        self.assertLess(d, np.finfo(float).tiny)

    def test_getRectFit(self):
        # Rectangle fit to the points with min area fitting
        bbox = np.array([[0,0], [1,0], [1,1], [0,1]])
        bp, center, size, orientation = utils.getRectFit(bbox, minAreaFit=True)
        self.assertListEqual(center, [0.5, 0.5])
        self.assertListEqual(size, [1, 1])
        self.assertEqual(orientation, 90.0)

        # Rectangle fit to the points without min area fitting
        bp, center, size, orientation = utils.getRectFit(bbox, minAreaFit=False)
        self.assertListEqual(center, [0.5, 0.5])
        self.assertListEqual(size, [1, 1])
        self.assertEqual(orientation, 0)

        # Size of the bounding rectangle if it contains only one point
        bbox = np.array([[1.2, 2.1]])
        bp, center, size, orientation = utils.getRectFit(bbox, minAreaFit=True)
        self.assertIsNone(np.testing.assert_array_equal(center, bbox.squeeze()))
        self.assertListEqual(size, [0., 0.])

    def test_filterPoints(self):
        # Checking size of filtered points
        bbox = np.array([[0,0], [1,0], [1,1], [0,1], [0, 0]])
        point = np.array([[0.1, 0.5]])
        filtered_points = utils.filterPoints(bbox, point)
        self.assertTupleEqual(filtered_points.shape, (0,2))

        point = np.array([[0.5, 0.5]])
        filtered_points = utils.filterPoints(bbox, point)
        self.assertTupleEqual(filtered_points.shape, (1,2))
    
    def test_boundsWithMinArea(self):
        width, height = 15, 10
        maxlevel = 5
        angles = list(range(0,100,10))
        L1 = [10,10.154,10.642,8,6.57,7.779,10,15.962,15.231,15]
        L2 = [15,15.231,15.963,10,7.779,7.779,11.547,10.642,10.154,10]
        dataset = utils.getDataset(L1, L2, angles, width, height)
        bpoints, *_ = utils.getRectFit(dataset, minAreaFit=True)
        filtered_dataset = utils.filterPoints(bpoints, dataset)
        _, center, size, orientation = utils.getRectFit(filtered_dataset, minAreaFit=True)
        self.assertListEqual(center, [6.85344765625, 5.53761875])
        self.assertListEqual(size, [1.83545078125, 6.077576171875])
        self.assertEqual(orientation, 80.82377624511719)
    
    def test_boundsWithoutMinArea(self):
        width, height = 15, 10
        maxlevel = 5
        angles = list(range(0,100,10))
        L1 = [10,10.154,10.642,8,6.57,7.779,10,15.962,15.231,15]
        L2 = [15,15.231,15.963,10,7.779,7.779,11.547,10.642,10.154,10]
        dataset = utils.getDataset(L1, L2, angles, width, height)
        bpoints, *_ = utils.getRectFit(dataset, minAreaFit=True)
        filtered_dataset = utils.filterPoints(bpoints, dataset)
        _, center, size, orientation = utils.getRectFit(filtered_dataset, minAreaFit=False)
        self.assertListEqual(center, [6.999877592124205, 5.964101615137754])
        self.assertListEqual(size, [5.999755184248411, 1.9282032302755105])
        self.assertEqual(orientation, 0.0)

if __name__ == '__main__':
    unittest.main()