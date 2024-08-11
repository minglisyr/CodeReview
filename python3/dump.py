# Pizza.py toolkit, www.cs.sandia.gov/~sjplimp/pizza.html
# Steve Plimpton, sjplimp@sandia.gov, Sandia National Laboratories
#
# Copyright (2005) Sandia Corporation.  Under the terms of Contract
# DE-AC04-94AL85000 with Sandia Corporation, the U.S. Government retains
# certain rights in this software.  This software is distributed under
# the GNU General Public License.

# dump tool

# Imports and external programs

from __future__ import print_function, absolute_import
import sys, re, glob, types
from os import popen
from math import *             # any function could be used by set()
import os
import functools

oneline = "Read, write, manipulate dump files and particle attributes"

docstr = """
d = dump("dump.one")              read in one or more dump files
d = dump("dump.1 dump.2.gz")      can be gzipped
d = dump("dump.*")                wildcard expands to multiple files
d = dump("dump.*",0)              two args = store filenames, but don't read

  incomplete and duplicate snapshots are deleted
  if atoms have 5 or 8 columns, assign id,type,x,y,z (ix,iy,iz)
  atoms will be unscaled if stored in files as scaled

time = d.next()                   read next snapshot from dump files

  used with 2-argument constructor to allow reading snapshots one-at-a-time
  snapshot will be skipped only if another snapshot has same time stamp
  return time stamp of snapshot read
  return -1 if no snapshots left or last snapshot is incomplete
  no column name assignment or unscaling is performed

d.map(1,"id",3,"x")               assign names to atom columns (1-N)

  not needed if dump file is self-describing

d.tselect.all()                   select all timesteps
d.tselect.one(N)                  select only timestep N
d.tselect.none()                  deselect all timesteps
d.tselect.skip(M)                 select every Mth step
d.tselect.test("$t >= 100 and $t < 10000")      select matching timesteps
d.delete()                        delete non-selected timesteps

  selecting a timestep also selects all atoms in the timestep
  skip() and test() only select from currently selected timesteps
  test() uses a Python Boolean expression with $t for timestep value
    Python comparison syntax: == != < > <= >= and or

d.aselect.all()                               select all atoms in all steps
d.aselect.all(N)                              select all atoms in one step
d.aselect.test("$id > 100 and $type == 2")    select match atoms in all steps
d.aselect.test("$id > 100 and $type == 2",N)  select matching atoms in one step

  all() with no args selects atoms from currently selected timesteps
  test() with one arg selects atoms from currently selected timesteps
  test() sub-selects from currently selected atoms
  test() uses a Python Boolean expression with $ for atom attributes
    Python comparison syntax: == != < > <= >= and or
    $name must end with a space

d.write("file")                    write selected steps/atoms to dump file
d.write("file",head,app)           write selected steps/atoms to dump file
d.scatter("tmp")                   write selected steps/atoms to multiple files

  write() can be specified with 2 additional flags
    head = 0/1 for no/yes snapshot header, app = 0/1 for write vs append
  scatter() files are given timestep suffix: e.g. tmp.0, tmp.100, etc

d.scale()                          scale x,y,z to 0-1 for all timesteps
d.scale(100)                       scale atom coords for timestep N
d.unscale()                        unscale x,y,z to box size to all timesteps
d.unscale(1000)                    unscale atom coords for timestep N
d.wrap()                           wrap x,y,z into periodic box via ix,iy,iz
d.unwrap()                         unwrap x,y,z out of box via ix,iy,iz
d.owrap("other")                   wrap x,y,z to same image as another atom
d.sort()                           sort atoms by atom ID in all selected steps
d.sort("x")                        sort atoms by column value in all steps
d.sort(1000)                       sort atoms in timestep N

  scale(), unscale(), wrap(), unwrap(), owrap() operate on all steps and atoms
  wrap(), unwrap(), owrap() require ix,iy,iz be defined
  owrap() requires a column be defined which contains an atom ID
    name of that column is the argument to owrap()
    x,y,z for each atom is wrapped to same image as the associated atom ID
    useful for wrapping all molecule's atoms the same so it is contiguous

m1,m2 = d.minmax("type")               find min/max values for a column
d.set("$ke = $vx * $vx + $vy * $vy")   set a column to a computed value
d.setv("type",vector)                  set a column to a vector of values
d.spread("ke",N,"color")               2nd col = N ints spread over 1st col
d.clone(1000,"color")                  clone timestep N values to other steps

  minmax() operates on selected timesteps and atoms
  set() operates on selected timesteps and atoms
    left hand side column is created if necessary
    left-hand side column is unset or unchanged for non-selected atoms
    equation is in Python syntax
    use $ for column names, $name must end with a space
  setv() operates on selected timesteps and atoms
    if column label does not exist, column is created
    values in vector are assigned sequentially to atoms, so may want to sort()
    length of vector must match # of selected atoms
  spread() operates on selected timesteps and atoms
    min and max are found for 1st specified column across all selected atoms
    atom's value is linear mapping (1-N) between min and max
    that is stored in 2nd column (created if needed)
    useful for creating a color map
  clone() operates on selected timesteps and atoms
    values at every timestep are set to value at timestep N for that atom ID
    useful for propagating a color map

t = d.time()                       return vector of selected timestep values
fx,fy,... = d.atom(100,"fx","fy",...)   return vector(s) for atom ID N
fx,fy,... = d.vecs(1000,"fx","fy",...)  return vector(s) for timestep N

  atom() returns vectors with one value for each selected timestep
  vecs() returns vectors with one value for each selected atom in the timestep

index,time,flag = d.iterator(0/1)          loop over dump snapshots
time,box,atoms,bonds,tris,lines = d.viz(index)   return list of viz objects
d.atype = "color"                          set column returned as "type" by viz
d.extra(obj)                               extract bond/tri/line info from obj

  iterator() loops over selected timesteps
  iterator() called with arg = 0 first time, with arg = 1 on subsequent calls
    index = index within dump object (0 to # of snapshots)
    time = timestep value
    flag = -1 when iteration is done, 1 otherwise
  viz() returns info for selected atoms for specified timestep index
    can also call as viz(time,1) and will find index of preceding snapshot
    time = timestep value
    box = \[xlo,ylo,zlo,xhi,yhi,zhi\]
    atoms = id,type,x,y,z for each atom as 2d array
    bonds = id,type,x1,y1,z1,x2,y2,z2,t1,t2 for each bond as 2d array
      if extra() used to define bonds, else NULL
    tris = id,type,x1,y1,z1,x2,y2,z2,x3,y3,z3,nx,ny,nz for each tri as 2d array
      if extra() used to define tris, else NULL
    lines = id,type,x1,y1,z1,x2,y2,z2 for each line as 2d array
      if extra() used to define lines, else NULL
  atype is column name viz() will return as atom type (def = "type")
  extra() extracts bonds/tris/lines from obj each time viz() is called
    obj can be data object for bonds, cdata object for tris and lines,
      bdump object for bonds, mdump object for tris, ldump object for lines
"""

# History
#   8/05, Steve Plimpton (SNL): original version
#   12/09, David Hart (SNL): allow use of NumPy or Numeric

# ToDo list
#   try to optimize this line in read_snap: words += f.readline().split()
#   allow $name in aselect.test() and set() to end with non-space
#   should next() snapshot be auto-unscaled ?

# Variables
#   flist = list of dump file names
#   increment = 1 if reading snapshots one-at-a-time
#   nextfile = which file to read from via next()
#   eof = ptr into current file for where to read via next()
#   scale_original = 0/1/-1 if coords were read in as unscaled/scaled/unknown
#   nsnaps = # of snapshots
#   nselect = # of selected snapshots
#   snaps = list of snapshots
#   names = dictionary of column names:
#     key = "id", value = column # (0 to M-1)
#   tselect = class for time selection
#   aselect = class for atom selection
#   atype = name of vector used as atom type by viz extract
#   bondflag = 0 if no bonds, 1 if they are defined statically, 2 if dynamic
#   bondlist = static list of bonds to return w/ viz() for all snapshots
#   triflag = 0 if no tris, 1 if they are defined statically, 2 if dynamic
#   trilist = static list of tris to return w/ viz() for all snapshots
#   lineflag = 0 if no lines, 1 if they are defined statically, 2 if dynamic
#   linelist = static list of lines to return w/ viz() for all snapshots
#   objextra = object to get bonds,tris,lines from dynamically
#   Snap = one snapshot
#     time = time stamp
#     tselect = 0/1 if this snapshot selected
#     natoms = # of atoms
#     nselect = # of selected atoms in this snapshot
#     aselect[i] = 0/1 for each atom
#     xlo,xhi,ylo,yhi,zlo,zhi = box bounds (float)
#     atoms[i][j] = 2d array of floats, i = 0 to natoms-1, j = 0 to ncols-1

try:
  import numpy as np
  oldnumeric = False
except:
  import Numeric as np
  oldnumeric = True

try: from DEFAULTS import PIZZA_GUNZIP
except: PIZZA_GUNZIP = "gunzip"

# Class definition

class dump:

  # --------------------------------------------------------------------

  def __init__(self,*input,**kwargs):

    self.snaps = []
    self.nsnaps = self.nselect = 0
    self.names = {}
    self.tselect = tselect(self)
    self.aselect = aselect(self)
    self.atype = "type"
    self.bondflag = 0
    self.bondlist = []
    self.triflag = 0
    self.trilist = []
    self.lineflag = 0
    self.linelist = []
    self.multiprocflag = 0
    self.fileNums = []
    self.objextra = None

    outputfl = True
    if isinstance(input[0],dict): # multiprocessing code (the [0] comes from the asteriks in the argumentlist)
      dictionary = input[0]

      # check whether to output or not
      if "debugMode" in dictionary: outputfl = dictionary["debugMode"]

      if outputfl: print("number of subprocess:", os.getpid())

      self.flist = dictionary["filelist"]
      self.multiprocflag = 1
      self.increment = 0
      self.read_all(output=outputfl)
    else: # serial code
      # flist = list of all dump file names
      words = input[0].split()
      self.flist = []
      for word in words: self.flist += glob.glob(word)
      if len(self.flist) == 0 and len(input) == 1:
        raise Exception("no dump file specified")

      if len(input) == 1:
        self.increment = 0
        self.read_all(output=outputfl)
      else:
        self.increment = 1
        self.nextfile = 0
        self.eof = 0

  # --------------------------------------------------------------------

  def read_all(self, **kwargs):

    # read all snapshots from each file
    # test for gzipped files

    # check whether to output or not
    outputfl = True
    if "output" in kwargs: outputfl = kwargs["output"]

    if outputfl: print("reading dump file...")

    for i,file in enumerate(self.flist):
      if file[-3:] == ".gz":
        f = popen("%s -c %s" % (PIZZA_GUNZIP,file),'r')
      else: f = open(file,'r', encoding='ascii')

      snap = self.read_snapshot(f)
      while snap:
        self.snaps.append(snap)
        if outputfl: print(snap.time,end=' ')
        self.fileNums.append(snap.time)
        sys.stdout.flush()
        snap = self.read_snapshot(f)

      f.close()
      
    if outputfl: print()

    # sort entries by timestep, cull duplicates

    self.snaps.sort(key = functools.cmp_to_key(self.compare_time))
    self.fileNums.sort()
    self.cull()
    self.nsnaps = len(self.snaps)
    #print("read %d snapshots" % self.nsnaps)

    # select all timesteps and atoms

    self.tselect.all(output=outputfl)

    # set default names for atom columns if file wasn't self-describing

    if len(self.snaps) == 0:
      if outputfl: print("no column assignments made")
    elif len(self.names):
      if outputfl: print("assigned columns:",self.names2str())
    else:
      if outputfl: print("no column assignments made")
      pass

    # if snapshots are scaled, unscale them

    if ("x" not in self.names) or \
       ("y" not in self.names) or \
       ("z" not in self.names):
      print("dump scaling status is unknown")
    elif self.nsnaps > 0:
      if self.scale_original == 1: self.unscale()
      elif self.scale_original == 0:
        if outputfl: print("dump is already unscaled")
      else:
        if outputfl: print("dump scaling status is unknown")

  # --------------------------------------------------------------------
  # read next snapshot from list of files

  def next(self):

    if not self.increment: raise Exception("cannot read incrementally")

    # read next snapshot in current file using eof as pointer
    # if fail, try next file
    # if new snapshot time stamp already exists, read next snapshot

    while 1:
      f = open(self.flist[self.nextfile],'rb', encoding='ascii')
      f.seek(self.eof)
      snap = self.read_snapshot(f)
      if not snap:
        self.nextfile += 1
        if self.nextfile == len(self.flist): return -1
        f.close()
        self.eof = 0
        continue
      self.eof = f.tell()
      f.close()
      try:
        self.findtime(snap.time)
        continue
      except: break

    # select the new snapshot with all its atoms

    self.snaps.append(snap)
    self.fileNums.append(snap.time)
    snap = self.snaps[self.nsnaps]
    snap.tselect = 1
    snap.nselect = snap.natoms
    for i in range(snap.natoms): snap.aselect[i] = 1
    self.nsnaps += 1
    self.nselect += 1

    return snap.time

  # --------------------------------------------------------------------
  # read a single snapshot from file f
  # return snapshot or 0 if failed
  # assign column names if not already done and file is self-describing
  # set scale_original to 0/1/-1 for unscaled/scaled/unknown
  # convert xs,xu to x

  def read_snapshot(self,f):
    try:
      snap = Snap()
      item = f.readline()
      snap.time = int(f.readline().split()[0])    # just grab 1st field
      item = f.readline()
      snap.natoms = int(f.readline())

      snap.aselect = np.zeros(snap.natoms)

      item = f.readline()
      words = f.readline().split()
      snap.xlo,snap.xhi = float(words[0]),float(words[1])
      words = f.readline().split()
      snap.ylo,snap.yhi = float(words[0]),float(words[1])
      words = f.readline().split()
      snap.zlo,snap.zhi = float(words[0]),float(words[1])

      item = f.readline()
      if len(self.names) == 0:
        self.scale_original = -1
        xflag = yflag = zflag = -1
        words = item.split()[2:]
        if len(words):
          for i in range(len(words)):
            if words[i] == "x" or words[i] == "xu":
              xflag = 0
              self.names["x"] = i
            elif words[i] == "xs" or words[i] == "xsu":
              xflag = 1
              self.names["x"] = i
            elif words[i] == "y" or words[i] == "yu":
              yflag = 0
              self.names["y"] = i
            elif words[i] == "ys" or words[i] == "ysu":
              yflag = 1
              self.names["y"] = i
            elif words[i] == "z" or words[i] == "zu":
              zflag = 0
              self.names["z"] = i
            elif words[i] == "zs" or words[i] == "zsu":
              zflag = 1
              self.names["z"] = i
            else: self.names[words[i]] = i
          if xflag == 0 and yflag == 0 and zflag == 0: self.scale_original = 0
          if xflag == 1 and yflag == 1 and zflag == 1: self.scale_original = 1

      if snap.natoms:
        words = f.readline().split()
        ncol = len(words)
        for i in range(1,snap.natoms):
          words += f.readline().split()
        floats = list(map(float,words))
        if oldnumeric: atoms = np.zeros((snap.natoms,ncol),np.Float)
        else: atoms = np.zeros((snap.natoms,ncol),np.float)
        start = 0
        stop = ncol
        for i in range(snap.natoms):
          atoms[i] = floats[start:stop]
          start = stop
          stop += ncol
      else: atoms = None
      snap.atoms = atoms
      return snap
    except:
      return 0

  # --------------------------------------------------------------------
  # map atom column names

  def map(self,*pairs):
    if len(pairs) % 2 != 0:
      raise Exception("dump map() requires pairs of mappings")
    for i in range(0,len(pairs),2):
      j = i + 1
      self.names[pairs[j]] = pairs[i]-1

  # --------------------------------------------------------------------
  # delete unselected snapshots

  def delete(self):
    ndel = i = 0
    while i < self.nsnaps:
      if not self.snaps[i].tselect:
        #del self.fileNums[i]
        del self.snaps[i]
        self.nsnaps -= 1
        ndel += 1
      else: i += 1
    print("%d snapshots deleted" % ndel)
    print("%d snapshots remaining" % self.nsnaps)

  # --------------------------------------------------------------------
  # scale coords to 0-1 for all snapshots or just one

  def scale(self,*dumplist):
    if len(dumplist) == 0:
      print("Scaling dump ...")
      x = self.names["x"]
      y = self.names["y"]
      z = self.names["z"]
      for snap in self.snaps: self.scale_one(snap,x,y,z)
    else:
      i = self.findtime(dumplist[0])
      x = self.names["x"]
      y = self.names["y"]
      z = self.names["z"]
      self.scale_one(self.snaps[i],x,y,z)

  # --------------------------------------------------------------------

  def scale_one(self,snap,x,y,z):
    xprdinv = 1.0 / (snap.xhi - snap.xlo)
    yprdinv = 1.0 / (snap.yhi - snap.ylo)
    zprdinv = 1.0 / (snap.zhi - snap.zlo)
    atoms = snap.atoms
    atoms[:,x] = (atoms[:,x] - snap.xlo) * xprdinv
    atoms[:,y] = (atoms[:,y] - snap.ylo) * yprdinv
    atoms[:,z] = (atoms[:,z] - snap.zlo) * zprdinv

  # --------------------------------------------------------------------
  # unscale coords from 0-1 to box size for all snapshots or just one

  def unscale(self,*dumplist):
    if len(dumplist) == 0:
      print("Unscaling dump ...")
      x = self.names["x"]
      y = self.names["y"]
      z = self.names["z"]
      for snap in self.snaps: self.unscale_one(snap,x,y,z)
    else:
      i = self.findtime(dumplist[0])
      x = self.names["x"]
      y = self.names["y"]
      z = self.names["z"]
      self.unscale_one(self.snaps[i],x,y,z)

  # --------------------------------------------------------------------

  def unscale_one(self,snap,x,y,z):
    xprd = snap.xhi - snap.xlo
    yprd = snap.yhi - snap.ylo
    zprd = snap.zhi - snap.zlo
    atoms = snap.atoms
    atoms[:,x] = snap.xlo + atoms[:,x]*xprd
    atoms[:,y] = snap.ylo + atoms[:,y]*yprd
    atoms[:,z] = snap.zlo + atoms[:,z]*zprd

  # --------------------------------------------------------------------
  # wrap coords from outside box to inside

  def wrap(self):
    print("Wrapping dump ...")

    x = self.names["x"]
    y = self.names["y"]
    z = self.names["z"]
    ix = self.names["ix"]
    iy = self.names["iy"]
    iz = self.names["iz"]

    for snap in self.snaps:
      xprd = snap.xhi - snap.xlo
      yprd = snap.yhi - snap.ylo
      zprd = snap.zhi - snap.zlo
      atoms = snap.atoms
      atoms[:,x] -= atoms[:,ix]*xprd
      atoms[:,y] -= atoms[:,iy]*yprd
      atoms[:,z] -= atoms[:,iz]*zprd

  # --------------------------------------------------------------------
  # unwrap coords from inside box to outside

  def unwrap(self):
    print("Unwrapping dump ...")

    x = self.names["x"]
    y = self.names["y"]
    z = self.names["z"]
    ix = self.names["ix"]
    iy = self.names["iy"]
    iz = self.names["iz"]

    for snap in self.snaps:
      xprd = snap.xhi - snap.xlo
      yprd = snap.yhi - snap.ylo
      zprd = snap.zhi - snap.zlo
      atoms = snap.atoms
      atoms[:,x] += atoms[:,ix]*xprd
      atoms[:,y] += atoms[:,iy]*yprd
      atoms[:,z] += atoms[:,iz]*zprd

  # --------------------------------------------------------------------
  # wrap coords to same image as atom ID stored in "other" column
  # if dynamic extra lines or triangles defined, owrap them as well

  def owrap(self,other):
    print("Wrapping to other ...")

    id = self.names["id"]
    x = self.names["x"]
    y = self.names["y"]
    z = self.names["z"]
    ix = self.names["ix"]
    iy = self.names["iy"]
    iz = self.names["iz"]
    iother = self.names[other]

    for snap in self.snaps:
      xprd = snap.xhi - snap.xlo
      yprd = snap.yhi - snap.ylo
      zprd = snap.zhi - snap.zlo
      atoms = snap.atoms
      ids = {}
      for i in range(snap.natoms):
        ids[atoms[i][id]] = i
      for i in range(snap.natoms):
        j = ids[atoms[i][iother]]
        atoms[i][x] += (atoms[i][ix]-atoms[j][ix])*xprd
        atoms[i][y] += (atoms[i][iy]-atoms[j][iy])*yprd
        atoms[i][z] += (atoms[i][iz]-atoms[j][iz])*zprd
      # should bonds also be owrapped ?
      if self.lineflag == 2 or self.triflag == 2:
        self.objextra.owrap(snap.time,xprd,yprd,zprd,ids,atoms,iother,ix,iy,iz)

  # --------------------------------------------------------------------
  # convert column names assignment to a string, in column order

  def names2str(self):
    pairs = list(self.names.items())
    values = list(self.names.values())
    ncol = len(pairs)
    str = ""
    for i in range(ncol):
      if i in values: str += pairs[values.index(i)][0] + ' '
    return str

  # --------------------------------------------------------------------
  # sort atoms by atom ID in all selected timesteps by default
  # if arg = string, sort all steps by that column
  # if arg = numeric, sort atoms in single step

  def sort(self,*tslist, **kwargs):

    # check whether to output or not
    outputfl = True
    if "output" in kwargs: outputfl = kwargs["output"]

    if len(tslist) == 0:
      if outputfl: print("Sorting selected snapshots ...")
      id = self.names["id"]
      for snap in self.snaps:
        if snap.tselect: self.sort_one(snap,id)
    elif isinstance(tslist[0], str):
      if outputfl: print("Sorting selected snapshots by %s ..." % tslist[0])
      id = self.names[tslist[0]]
      for snap in self.snaps:
        if snap.tselect: self.sort_one(snap,id)
    else:
      i = self.findtime(tslist[0])
      id = self.names["id"]
      self.sort_one(self.snaps[i],id)

  # --------------------------------------------------------------------
  # sort a single snapshot by ID column

  def sort_one(self,snap,id):
    atoms = snap.atoms
    ids = atoms[:,id]
    ordering = np.argsort(ids)
    for i in range(len(atoms[0])):
      atoms[:,i] = np.take(atoms[:,i],ordering)

  # --------------------------------------------------------------------
  # write a single dump file from current selection

  def write(self,file,header=1,append=0):
    if len(self.snaps): namestr = self.names2str()
    if not append: f = open(file,"w", encoding='ascii')
    else: f = open(file,"a", encoding='ascii')
    for snap in self.snaps:
      if not snap.tselect: continue
      print(snap.time, end=' ')
      sys.stdout.flush()

      if header:
        print("ITEM: TIMESTEP", file=f)
        print(snap.time, file=f)
        print("ITEM: NUMBER OF ATOMS", file=f)
        print(snap.nselect, file=f)
        print("ITEM: BOX BOUNDS", file=f)
        print(snap.xlo,snap.xhi, file=f)
        print(snap.ylo,snap.yhi, file=f)
        print(snap.zlo,snap.zhi, file=f)
        print("ITEM: ATOMS",namestr, file=f)

      atoms = snap.atoms
      nvalues = len(atoms[0])
      for i in range(snap.natoms):
        if not snap.aselect[i]: continue
        line = ""
        for j in range(nvalues):
          if (j < 2):
            line += str(int(atoms[i][j])) + " "
          else:
            line += str(atoms[i][j]) + " "
        print(line, file=f)
    f.close()
    print("\n%d snapshots" % self.nselect)

  # --------------------------------------------------------------------
  # write one dump file per snapshot from current selection

  def scatter(self,root):
    if len(self.snaps): namestr = self.names2str()
    for snap in self.snaps:
      if not snap.tselect: continue
      print(snap.time, end=' ')
      sys.stdout.flush()

      file = root + "." + str(snap.time)
      f = open(file,"w", encoding='ascii')
      print("ITEM: TIMESTEP", file=f)
      print(snap.time, file=f)
      print("ITEM: NUMBER OF ATOMS", file=f)
      print(snap.nselect, file=f)
      print("ITEM: BOX BOUNDS", file=f)
      print(snap.xlo,snap.xhi, file=f)
      print(snap.ylo,snap.yhi, file=f)
      print(snap.zlo,snap.zhi, file=f)
      print("ITEM: ATOMS",namestr, file=f)

      atoms = snap.atoms
      nvalues = len(atoms[0])
      for i in range(snap.natoms):
        if not snap.aselect[i]: continue
        line = ""
        for j in range(nvalues):
          if (j < 2):
            line += str(int(atoms[i][j])) + " "
          else:
            line += str(atoms[i][j]) + " "
        print(line, file=f)
      f.close()
    print("\n%d snapshots" % self.nselect)

  # --------------------------------------------------------------------
  # find min/max across all selected snapshots/atoms for a particular column

  def minmax(self,colname):
    icol = self.names[colname]
    min = 1.0e20
    max = -min
    for snap in self.snaps:
      if not snap.tselect: continue
      atoms = snap.atoms
      for i in range(snap.natoms):
        if not snap.aselect[i]: continue
        if atoms[i][icol] < min: min = atoms[i][icol]
        if atoms[i][icol] > max: max = atoms[i][icol]
    return (min,max)

  # --------------------------------------------------------------------
  # set a column value via an equation for all selected snapshots

  def set(self,eq):
    print("Setting ...")
    pattern = "\$\w*"
    eqlist = re.findall(pattern,eq)

    lhs = eqlist[0][1:]
    if lhs not in self.names:
      self.newcolumn(lhs)

    for item in eqlist:
      name = item[1:]
      column = self.names[name]
      insert = "snap.atoms[i][%d]" % (column)
      eq = eq.replace(item,insert)
    ceq = compile(eq,'','single')

    for snap in self.snaps:
      if not snap.tselect: continue
      for i in range(snap.natoms):
        if snap.aselect[i]: exec(ceq)

  # --------------------------------------------------------------------
  # set a column value via an input vec for all selected snapshots/atoms

  def setv(self,colname,vec):
    print("Setting ...")
    if colname not in self.names:
      self.newcolumn(colname)
    icol = self.names[colname]

    for snap in self.snaps:
      if not snap.tselect: continue
      if snap.nselect != len(vec):
        raise Exception("vec length does not match # of selected atoms")
      atoms = snap.atoms
      m = 0
      for i in range(snap.natoms):
        if snap.aselect[i]:
          atoms[i][icol] = vec[m]
          m += 1

  # --------------------------------------------------------------------
  # clone value in col across selected timesteps for atoms with same ID

  def clone(self,nstep,col):
    istep = self.findtime(nstep)
    icol = self.names[col]
    id = self.names["id"]
    ids = {}
    for i in range(self.snaps[istep].natoms):
      ids[self.snaps[istep].atoms[i][id]] = i
    for snap in self.snaps:
      if not snap.tselect: continue
      atoms = snap.atoms
      for i in range(snap.natoms):
        if not snap.aselect[i]: continue
        j = ids[atoms[i][id]]
        atoms[i][icol] = self.snaps[istep].atoms[j][icol]

  # --------------------------------------------------------------------
  # values in old column are spread as ints from 1-N and assigned to new column

  def spread(self,old,n,new):
    iold = self.names[old]
    if new not in self.names: self.newcolumn(new)
    inew = self.names[new]

    min,max = self.minmax(old)
    print("min/max = ",min,max)

    gap = max - min
    invdelta = n/gap
    for snap in self.snaps:
      if not snap.tselect: continue
      atoms = snap.atoms
      for i in range(snap.natoms):
        if not snap.aselect[i]: continue
        ivalue = int((atoms[i][iold] - min) * invdelta) + 1
        if ivalue > n: ivalue = n
        if ivalue < 1: ivalue = 1
        atoms[i][inew] = ivalue

  # --------------------------------------------------------------------
  # return vector of selected snapshot time stamps

  def time(self):
    vec = self.nselect * [0]
    i = 0
    for snap in self.snaps:
      if not snap.tselect: continue
      vec[i] = snap.time
      i += 1
    return vec

  # --------------------------------------------------------------------
  # extract vector(s) of values for atom ID n at each selected timestep

  def atom(self,n,*tslist):
    if len(tslist) == 0:
      raise Exception("no columns specified")
    columns = []
    values = []
    for name in tslist:
      columns.append(self.names[name])
      values.append(self.nselect * [0])
    ncol = len(columns)

    id = self.names["id"]
    m = 0
    for snap in self.snaps:
      if not snap.tselect: continue
      atoms = snap.atoms
      for i in range(snap.natoms):
        if atoms[i][id] == n: break
      if atoms[i][id] != n:
        raise Exception("could not find atom ID in snapshot")
      for j in range(ncol):
        values[j][m] = atoms[i][columns[j]]
      m += 1

    if len(tslist) == 1: return values[0]
    else: return values

  # --------------------------------------------------------------------
  # extract vector(s) of values for selected atoms at chosen timestep

  def vecs(self,n,*tslist):
    snap = self.snaps[self.findtime(n)]

    if len(tslist) == 0:
      raise Exception("no columns specified")
    columns = []
    values = []
    for name in tslist:
      columns.append(self.names[name])
      values.append(snap.nselect * [0])
    ncol = len(columns)

    m = 0
    for i in range(snap.natoms):
      if not snap.aselect[i]: continue
      for j in range(ncol):
        values[j][m] = snap.atoms[i][columns[j]]
      m += 1

    if len(tslist) == 1: return values[0]
    else: return values

  # --------------------------------------------------------------------
  # add a new column to every snapshot and set value to 0
  # set the name of the column to str

  def newcolumn(self,str):
    ncol = len(self.snaps[0].atoms[0])
    self.map(ncol+1,str)
    for snap in self.snaps:
      atoms = snap.atoms
      if oldnumeric: newatoms = np.zeros((snap.natoms,ncol+1),np.Float)
      else: newatoms = np.zeros((snap.natoms,ncol+1),np.float)
      newatoms[:,0:ncol] = snap.atoms
      snap.atoms = newatoms

  # --------------------------------------------------------------------
  # sort snapshots on time stamp

  def compare_time(self,a,b):
    if a.time < b.time:
      return -1
    elif a.time > b.time:
      return 1
    else:
      return 0

  # --------------------------------------------------------------------
  # delete successive snapshots with duplicate time stamp

  def cull(self):
    i = 1
    while i < len(self.snaps):
      if self.snaps[i].time == self.snaps[i-1].time:
        del self.snaps[i]
      else:
        i += 1

  # --------------------------------------------------------------------
  # iterate over selected snapshots

  def iterator(self,flag):
    start = 0
    if flag: start = self.iterate + 1
    for i in range(start,self.nsnaps):
      if self.snaps[i].tselect:
        self.iterate = i
        return i,self.snaps[i].time,1
    return 0,0,-1

  # --------------------------------------------------------------------
  # return list of atoms to viz for snapshot isnap
  # if called with flag, then index is timestep, so convert to snapshot index
  # augment with bonds, tris, lines if extra() was invoked

  def viz(self,index,flag=0):
    if not flag: isnap = index
    else:
      times = self.time()
      n = len(times)
      i = 0
      while i < n:
        if times[i] > index: break
        i += 1
      isnap = i - 1

    snap = self.snaps[isnap]

    time = snap.time
    box = [snap.xlo,snap.ylo,snap.zlo,snap.xhi,snap.yhi,snap.zhi]
    id = self.names["id"]
    type = self.names[self.atype]
    x = self.names["x"]
    y = self.names["y"]
    z = self.names["z"]

    # create atom list needed by viz from id,type,x,y,z
    # need Numeric/Numpy mode here

    atoms = []
    for i in range(snap.natoms):
      if not snap.aselect[i]: continue
      atom = snap.atoms[i]
      atoms.append([atom[id],atom[type],atom[x],atom[y],atom[z]])

    # create list of bonds from static or dynamic bond list
    # then generate bond coords from bondlist
    # alist = dictionary of atom IDs for atoms list
    # lookup bond atom IDs in alist and grab their coords
    # try is used since some atoms may be unselected
    #   any bond with unselected atom is not added to bonds
    # need Numeric/Numpy mode here

    bonds = []
    if self.bondflag:
      if self.bondflag == 1: bondlist = self.bondlist
      elif self.bondflag == 2:
        tmp1,tmp2,tmp3,bondlist,tmp4,tmp5 = self.objextra.viz(time,1)
      alist = {}
      for i in range(len(atoms)): alist[int(atoms[i][0])] = i
      for bond in bondlist:
        try:
          i = alist[bond[2]]
          j = alist[bond[3]]
          atom1 = atoms[i]
          atom2 = atoms[j]
          bonds.append([bond[0],bond[1],atom1[2],atom1[3],atom1[4],
                        atom2[2],atom2[3],atom2[4],atom1[1],atom2[1]])
        except: continue

    # create list of tris from static or dynamic tri list
    # if dynamic, could eliminate tris for unselected atoms

    tris = []
    if self.triflag:
      if self.triflag == 1: tris = self.trilist
      elif self.triflag == 2:
        tmp1,tmp2,tmp3,tmp4,tris,tmp5 = self.objextra.viz(time,1)

    # create list of lines from static or dynamic tri list
    # if dynamic, could eliminate lines for unselected atoms

    lines = []
    if self.lineflag:
      if self.lineflag == 1: lines = self.linelist
      elif self.lineflag == 2:
        tmp1,tmp2,tmp3,tmp4,tmp5,lines = self.objextra.viz(time,1)

    return time,box,atoms,bonds,tris,lines

  # --------------------------------------------------------------------

  def findtime(self,n):
    for i in range(self.nsnaps):
      if self.snaps[i].time == n: return i
    raise Exception("no step %d exists" % n)

  # --------------------------------------------------------------------
  # return maximum box size across all selected snapshots

  def maxbox(self):
    xlo = ylo = zlo = None
    xhi = yhi = zhi = None
    for snap in self.snaps:
      if not snap.tselect: continue
      if xlo == None or snap.xlo < xlo: xlo = snap.xlo
      if xhi == None or snap.xhi > xhi: xhi = snap.xhi
      if ylo == None or snap.ylo < ylo: ylo = snap.ylo
      if yhi == None or snap.yhi > yhi: yhi = snap.yhi
      if zlo == None or snap.zlo < zlo: zlo = snap.zlo
      if zhi == None or snap.zhi > zhi: zhi = snap.zhi
    return [xlo,ylo,zlo,xhi,yhi,zhi]

  # --------------------------------------------------------------------
  # return maximum atom type across all selected snapshots and atoms

  def maxtype(self):
    icol = self.names["type"]
    max = 0
    for snap in self.snaps:
      if not snap.tselect: continue
      atoms = snap.atoms
      for i in range(snap.natoms):
        if not snap.aselect[i]: continue
        if atoms[i][icol] > max: max = atoms[i][icol]
    return int(max)

  # --------------------------------------------------------------------
  # grab bonds/tris/lines from another object
  # if static, grab once, else store obj to grab dynamically

  def extra(self,arg):

    # data object, grab bonds statically

    if isinstance(arg, object) and ".data" in str(arg.__class__):
      self.bondflag = 0
      try:
        bondlist = []
        bondlines = arg.sections["Bonds"]
        for line in bondlines:
          words = line.split()
          bondlist.append([int(words[0]),int(words[1]),
                           int(words[2]),int(words[3])])
        if bondlist:
          self.bondflag = 1
          self.bondlist = bondlist
      except:
        raise Exception("could not extract bonds from data object")

    # cdata object, grab tris and lines statically

    elif isinstance(arg, object) and ".cdata" in str(arg.__class__):
      self.triflag = self.lineflag = 0
      try:
        tmp,tmp,tmp,tmp,tris,lines = arg.viz(0)
        if tris:
          self.triflag = 1
          self.trilist = tris
        if lines:
          self.lineflag = 1
          self.linelist = lines
      except:
        raise Exception("could not extract tris/lines from cdata object")

    # mdump object, grab tris dynamically

    elif isinstance(arg, object) and ".mdump" in str(arg.__class__):
      self.triflag = 2
      self.objextra = arg

    # bdump object, grab bonds dynamically

    elif isinstance(arg, object) and ".bdump" in str(arg.__class__):
      self.bondflag = 2
      self.objextra = arg

    # ldump object, grab tris dynamically

    elif isinstance(arg, object) and ".ldump" in str(arg.__class__):
      self.lineflag = 2
      self.objextra = arg

    # tdump object, grab tris dynamically

    elif isinstance(arg, object) and ".tdump" in str(arg.__class__):
      self.triflag = 2
      self.objextra = arg

    else:
      raise Exception("unrecognized argument to dump.extra()")

  # --------------------------------------------------------------------

  def compare_atom(self,a,b):
    if a[0] < b[0]:
      return -1
    elif a[0] > b[0]:
      return 1
    else:
      return 0

# --------------------------------------------------------------------
# one snapshot

class Snap:
  pass

# --------------------------------------------------------------------
# time selection class

class tselect:

  def __init__(self,data):
    self.data = data

  # --------------------------------------------------------------------

  def all(self,**kwargs):

    # check whether to output or not
    outputfl = True
    if "output" in kwargs: outputfl = kwargs["output"]

    data = self.data
    for snap in data.snaps:
      snap.tselect = 1
    data.nselect = len(data.snaps)
    data.aselect.all()
    if outputfl: print("%d snapshots selected out of %d" % (data.nselect,data.nsnaps))

  # --------------------------------------------------------------------

  def one(self,n):
    data = self.data
    for snap in data.snaps:
      snap.tselect = 0
    i = data.findtime(n)
    data.snaps[i].tselect = 1
    data.nselect = 1
    data.aselect.all()
    print("%d snapshots selected out of %d" % (data.nselect,data.nsnaps))

  # --------------------------------------------------------------------

  def none(self):
    data = self.data
    for snap in data.snaps:
      snap.tselect = 0
    data.nselect = 0
    print("%d snapshots selected out of %d" % (data.nselect,data.nsnaps))

  # --------------------------------------------------------------------

  def skip(self,n):
    data = self.data
    count = n-1
    for snap in data.snaps:
      if not snap.tselect: continue
      count += 1
      if count == n:
        count = 0
        continue
      snap.tselect = 0
      data.nselect -= 1
    data.aselect.all()
    print("%d snapshots selected out of %d" % (data.nselect,data.nsnaps))

  # --------------------------------------------------------------------

  def test(self,teststr):
    data = self.data
    snaps = data.snaps
    cmd = "flag = " + teststr.replace("$t","snaps[i].time")
    ccmd = compile(cmd,'','single')
    for i in range(data.nsnaps):
      if not snaps[i].tselect: continue
      ldict = {'data':data,'snaps':snaps,'i':i}
      exec(ccmd,globals(),ldict)
      flag = ldict['flag']
      if not flag:
        snaps[i].tselect = 0
        data.nselect -= 1
    data.aselect.all()
    print("%d snapshots selected out of %d" % (data.nselect,data.nsnaps))

# --------------------------------------------------------------------
# atom selection class

class aselect:

  def __init__(self,data):
    self.data = data

  # --------------------------------------------------------------------

  def all(self,*args):
    data = self.data
    if len(args) == 0:                           # all selected timesteps
      for snap in data.snaps:
        if not snap.tselect: continue
        for i in range(snap.natoms): snap.aselect[i] = 1
        snap.nselect = snap.natoms
    else:                                        # one timestep
      n = data.findtime(args[0])
      snap = data.snaps[n]
      for i in range(snap.natoms): snap.aselect[i] = 1
      snap.nselect = snap.natoms

  # --------------------------------------------------------------------

  def test(self,teststr,*args):
    data = self.data

    # replace all $var with snap.atoms references and compile test string

    pattern = "\$\w*"
    testlist = re.findall(pattern,teststr)
    for item in testlist:
      name = item[1:]
      column = data.names[name]
      insert = "snap.atoms[i][%d]" % column
      teststr = teststr.replace(item,insert)
    cmd = "flag = " + teststr
    ccmd = compile(cmd,'','single')

    if len(args) == 0:                           # all selected timesteps
      for snap in data.snaps:
        if not snap.tselect: continue
        for i in range(snap.natoms):
          if not snap.aselect[i]: continue
          ldict = {'snap':snap,'i':i}
          exec(ccmd,globals(),ldict)
          flag = ldict['flag']
          if not flag:
            snap.aselect[i] = 0
            snap.nselect -= 1
      for i in range(data.nsnaps):
        if data.snaps[i].tselect:
          print("%d atoms of %d selected in first step %d" % \
                (data.snaps[i].nselect,data.snaps[i].natoms,data.snaps[i].time))
          break
      for i in range(data.nsnaps-1,-1,-1):
        if data.snaps[i].tselect:
          print("%d atoms of %d selected in last step %d" % \
                (data.snaps[i].nselect,data.snaps[i].natoms,data.snaps[i].time))
          break

    else:                                        # one timestep
      n = data.findtime(args[0])
      snap = data.snaps[n]
      for i in range(snap.natoms):
        if not snap.aselect[i]: continue
        ldict = {'snap':snap,'i':i}
        exec(ccmd,globals(),ldict)
        flag = ldict['flag']
        if not flag:
          snap.aselect[i] = 0
          snap.nselect -= 1
