import numpy as np
import quadtreemap
import cv2

np.set_printoptions(suppress=True, precision=2)

def getDataset(L1, L2, angle_list, width, height):
    angles = np.deg2rad(angle_list)
    L1_val = np.array(L1)
    L2_val = np.array(L2)

    L1_xy = np.vstack([L1_val*np.sin(angles), L1_val*np.cos(angles)])
    L2_xy = np.vstack([width - L2_val*np.cos(angles), L2_val*np.sin(angles)])

    # Dataset from lasers
    return np.vstack([L1_xy.transpose(), L2_xy.transpose()])

def shortDistanceToBox(bpoints, pp):
    # Distance between a point and line based on h = 2A/b formula
    # This is run through all sides of polygon to find closest distance
    pts = [bpoints[[i,i+1], :] for i in range(4)]
    dist = []
    x0, y0 = pp
    for pt in pts:
        x, y = pt[:,0], pt[:,1]
        base = np.linalg.norm([x[1]-x[0], y[1] - y[0]])
        d = abs((x[1] - x[0]) * (y[0] - y0) - (x[0] - x0) * (y[1] - y[0])) / base
        dist.append(d)
    
    return min(dist)

def getRectFit(points, minAreaFit=True):
    if minAreaFit:
        # This is the minimum area rectangle that can be fit on a set of points
        # Since cv2 works only in pixels/int, it is modified to operate with float at precision 4
        rect = cv2.minAreaRect(np.int32(points*1e4))
        centers = [val*1e-4 for val in rect[0]]
        size = [val*1e-4 for val in rect[1]]
        orientation = rect[2]
        bpoints = cv2.boxPoints(rect)*1e-4
    else:
        xmin = min(points[:,0])
        xmax = max(points[:,0])
        ymin = min(points[:,1])
        ymax = max(points[:,1])
        bpoints = np.array([[xmin, ymin], [xmax, ymin], [xmax, ymax], [xmin, ymax]])
        centers = [(xmax + xmin)/2, (ymax + ymin)/2]
        size = [abs(xmax - xmin), abs(ymax - ymin)]
        orientation = 0.0
    bpoints = np.vstack([bpoints,bpoints[0]])
    return bpoints, centers, size, orientation

def filterPoints(bpoints, dataset, threshold = 0.1):
    # Filtering out points closer to the bounding polygon based on threshold
    distances = []
    for p in dataset:
        distances.append(shortDistanceToBox(bpoints, p))
    filteredPoints = dataset[np.array(distances)>threshold,:]
    return filteredPoints

def generatePCDataFromBox(bpoints, minDis = 1):
    pts = [bpoints[[i,i+1], :] for i in range(4)]
    xl, yl = [], []
    for pt in pts:
        x, y = pt[:,0], pt[:,1]
        d = np.linalg.norm([x[1]-x[0], y[1] - y[0]])
        if abs(x[1] - x[0]) > 0:
            angle = np.arctan(abs(y[1] - y[0]) / abs(x[1] - x[0]))
        else:
            angle = np.pi/2
        
        xd = np.sign(x[1] - x[0]) * minDis * np.cos(angle)
        yd = np.sign(y[1] - y[0]) * minDis * np.sin(angle)
        xn = x[0]
        yn = y[0]
        xl.append(xn)
        yl.append(yn)
        for _ in range(np.int0(d/minDis)):
            xn += xd
            yn += yd
            xl.append(xn)
            yl.append(yn)
    
    return np.vstack([xl, yl]).T

def fillBoxWithPoints(rect, sampling=10):
    center, size, orientation = rect
    xmin, ymin = center[0] - size[0]/2, center[1] - size[1]/2
    xmax, ymax = center[0] + size[0]/2, center[1] + size[1]/2
    xx, yy = np.meshgrid(np.linspace(xmin, xmax, sampling), np.linspace(ymin, ymax, sampling))
    ori = np.deg2rad(orientation)
    c, s = np.cos(ori), np.sin(ori)
    rot = np.array([[c, -s], [s, c]])
    pts = np.array([[xa, ya] for xa,ya in zip(xx.flatten(), yy.flatten())])
    return (pts - np.array(center)).dot(rot.T) + np.array(center)

def Kmeans(X, K=1, n_iter=10):
    m = X.shape[0] # number of training examples
    n = X.shape[1] # number of features. n = 2
    Centroids = np.array([]).reshape(n, 0)
    idx = np.random.randint(0, m-1, size=K)
    Centroids = X[idx, :]
    for _ in range(n_iter):
        distance = np.array([]).reshape(m, 0)
        for k in range(K):
            tempDist = np.sum((X-Centroids[k, :])**2, axis=1)
            distance = np.c_[distance, tempDist]

        C = np.argmin(distance, axis=1)+1

        Y = {}
        for k in range(K):
            Y[k+1] = np.array([]).reshape(n, 0)
        for i in range(m):
            Y[C[i]] = np.c_[Y[C[i]], X[i]]

            # Regrouping to nearby centroids
        for k in range(K):
            Y[k+1] = Y[k+1].T

        for k in range(K):
            Centroids[k,:] = np.mean(Y[k+1], axis=0)
        Output = Y
    return Output, Centroids


class Perception:
    def __init__(self, dataset=None):
        if dataset is not None:
            self.dataset = dataset
        else:
            print("No dataset is presented with.")
        self.obstacles_detected = []
    
    def boundaryDetection(self):
        # Getting outer bounding box from rectangle fit
        self.bpoints, *_ = getRectFit(self.dataset, minAreaFit=True)
        self.filtered_dataset = filterPoints(self.bpoints, self.dataset)
        

    def obstacleDetection(self, no_obj=1, minAreaFit=True):
        # Filter out data points near bounding box
        obstacles_cluster, _ = Kmeans(self.filtered_dataset, K=no_obj, n_iter=10)

        # Finding bounding box for obstacle
        for obstacle_data in obstacles_cluster.values():
            obstacle, *properties = getRectFit(obstacle_data, minAreaFit=minAreaFit)
            finer_pts = fillBoxWithPoints(properties, sampling=50)
            self.obstacles_detected.append({
                "boundary":obstacle,
                "data":finer_pts,
                "center":properties[0],
                "size":properties[1],
                "orientation":properties[2]
                })

    def generateOccupance_gridmap(self, boundary, maxlevel):
        width, height = boundary
        # Quadtree occupancy grid
        boundbox = quadtreemap.Rectangle(0-0.5, 0-0.5, width+0.5, height+0.5)
        self.map = quadtreemap.QuadTree(boundbox, maxlevel)
        self.tapp = quadtreemap.Tree(width, height)
        
        finer_bpoints = generatePCDataFromBox(self.bpoints, minDis=0.1)
        boundingBox = quadtreemap.PointCloud(finer_bpoints)
        self.map.insert(boundingBox)

        for obstacle in self.obstacles_detected:
            obstacleBox = quadtreemap.PointCloud(obstacle["data"])
            self.map.insert(obstacleBox)

    def drawOccupancyGrid(self, save=False, fname="graph.png"):
        self.tapp.drawTree(self.map.root)
        self.tapp.drawBounds(self.bpoints)
        for obstacle in self.obstacles_detected:
            self.tapp.drawBounds(obstacle["boundary"])
        
        self.tapp.drawPCData(self.dataset)
        self.tapp.draw(save, fname)
    
    def detectionSummary(self):
        output = "Detection:\n\n"
        for i, obs in enumerate(self.obstacles_detected):
            output += f"Object {i+1}:\n"
            output += f"\tBounds: {obs['boundary']}\n"
            output += f"\tCenter: ({obs['center'][0]:.2f}, {obs['center'][1]:.2f})\n"
            output += f"\tDimension (m): Width: {obs['size'][0]:.2f}\Length: {obs['size'][1]:.2f}\n"
            output += f"\tOrientation (deg): {obs['orientation']:.2f}\n\n"
        
        return output