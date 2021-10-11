import utils

'''
Table of values
Angle       L1      L2
(degrees)   (m)     (m)
0           10      15
10          10.154  15.231
20          10.642  15.963
30          8       10
40          6.57    7.779
50          7.779   7.779
60          10      11.547
70          15.962  10.642
80          15.231  10.154
90          15      10
'''

def main():
    width, height = 15, 10
    maxlevel = 5

    angles = list(range(0,100,10))
    L1 = [10,10.154,10.642,8,6.57,7.779,10,15.962,15.231,15]
    L2 = [15,15.231,15.963,10,7.779,7.779,11.547,10.642,10.154,10]

    dataset = utils.getDataset(L1, L2, angles, width, height)

    perception = utils.Perception(dataset)
    perception.boundaryDetection()
    perception.obstacleDetection(no_obj=1, minAreaFit=True)
    perception.generateOccupance_gridmap((width, height), maxlevel)
    perception.drawOccupancyGrid(save=False, fname="minAreaFit.png")

    print(perception.detectionSummary())

if __name__ == "__main__":
    main()