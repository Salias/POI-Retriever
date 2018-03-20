import sys
import time
import os
import math
import json
import geopy
import pandas as pd
import numpy as np
import shapefile as shp
import math
import multiprocessing as mp
from pyproj import Proj, transform
from geopy.distance import VincentyDistance
from shapely.geometry import box, mapping, shape


lon_km = 0.004491576420629531
lat_km = 0.0045218473851471735


import multiprocessing as mp
class ParallelBucket:
	def __init__(self, cpu_limit=True):
		self.jobs = []
		if cpu_limit:
			self.ncpus = mp.cpu_count()
		else:
			self.ncpus = float("inf")

	def add_job(self, func, args=()):
		t = mp.Process(target=func, args=args)
		t.start()
		self.jobs.append(t)

		if len(self.jobs) >= self.ncpus:
			self.joinall()

	def joinall(self):
		for job in self.jobs:
			job.join()
		self.jobs = []


def getShape(coords):
	minx, miny, maxx, maxy = coords
	return json.dumps(mapping(box(minx, miny, maxx, maxy)))

def convert_proj(coord, in_proj='epsg:3857', out_proj='epsg:4326'):
	inProj = Proj(init=in_proj)
	outProj = Proj(init=out_proj)
	x1, y1 = coord
	x2, y2 = transform(inProj, outProj, x1, y1)
	return [x2, y2]

def get_polygon(i, j, BB):
	maxx,maxy = BB[0]
	minx,miny = BB[1]
	dx = 1333.3333333333
	dy = 1333.3333333333
	vertices = []
	vertices.append(convert_proj([min(minx+dx*j,maxx), max(maxy-dy*i,miny)]))
	vertices.append(convert_proj([min(minx+dx*(j+1),maxx), max(maxy-dy*i,miny)]))
	vertices.append(convert_proj([min(minx+dx*(j+1),maxx), max(maxy-dy*(i+1),miny)]))
	vertices.append(convert_proj([min(minx+dx*j,maxx), max(maxy-dy*(i+1),miny)]))
	pol = np.array(vertices)
	bb = [pol[:,:1].min(), pol[:,1:].min(), pol[:,:1].max(), pol[:,1:].max()]

	return bb

def compute_subset(subset, BB, POLYGONS):
	for i, j in subset:
		bb = get_polygon(i, j, BB)
		POLYGONS.append(bb)

def make_grid(BB, cell_size):
	BB = [(BB[0], BB[1]), (BB[2], BB[3])]
	BB = [convert_proj(coord, in_proj='epsg:4326', out_proj='epsg:3857') for coord in BB]
	# minx,maxx,miny,maxy = 448262.080078, 450360.750122, 6262492.020081, 6262938.950073
	maxx,maxy = BB[0]
	minx,miny = BB[1]
	dx = 1333.3333333333
	dy = 1333.3333333333
	nx = int(math.ceil(abs(maxx - minx)/dx))
	ny = int(math.ceil(abs(maxy - miny)/dy))

	POLYGONS = mp.Manager().list()
	bucket = ParallelBucket()
	processed = 0
	count = 0
	total = ny*nx
	limit = total/mp.cpu_count()
	subset = []
	ts = time.time()
	for i in range(ny):
		for j in range(nx):
			subset.append((i, j))
			if processed == limit:
				# compute_subset(subset, BB, POLYGONS)
				print 'Computing -> ', count, ' of ', total
				bucket.add_job(compute_subset, args=(subset, BB, POLYGONS))
				subset = []
				processed = 0
			count += 1
			processed += 1
	bucket.joinall()

	print 'Computing Final ', len(subset)	
	POLYGONS = list(POLYGONS)
	compute_subset(subset, BB, POLYGONS)
	bucket.joinall()
	POLYGONS = map(getShape, list(POLYGONS))

	CENTROIDS = []
	i = 1
	for pol in POLYGONS:
		geojson = json.loads(pol)
		poly = shape(geojson)
		CENTROIDS.append([i, poly.centroid.x, poly.centroid.y])
		i += 1

	return pd.DataFrame(CENTROIDS, columns=['ID', 'lon', 'lat'])

