'''
Plot examples of features.

@author: dmitry.yarotsky
'''

import os
import numpy as np
import time
import scipy.linalg as linalg
from mayavi import mlab

import voxelfeatures as vf

import transforms 
  

def plotShape(kind, outline=False, title=True, save=False, **kwargs):
    f = mlab.figure(bgcolor=(1,1,1), size=(350,400))    
    spatialSize = float(kwargs['spatialSize'])  
    if outline:        
        for k in [-1,1]:
            for n in [-1,1]:
                L = [np.array([-1,1]), np.array([k,k]), np.array([n,n])]
                for d in range(3):
                    mlab.plot3d(spatialSize/2*L[d], spatialSize/2*L[(d+1)%3], spatialSize/2*L[(d+2)%3])        
    
    if kind == 'solid':
        vertA = kwargs['vertA']
        faceA = kwargs['faceA']
        mlab.triangular_mesh(vertA[:,0], vertA[:,1], vertA[:,2], faceA) 
    elif kind == 'transparent':
        vertA = kwargs['vertA']
        faceA = kwargs['faceA']
        mlab.triangular_mesh(vertA[:,0], vertA[:,1], vertA[:,2], faceA, opacity=0.1) 
    elif kind == 'wireframe':
        vertA = kwargs['vertA']
        faceA = kwargs['faceA']
        mlab.triangular_mesh(vertA[:,0], vertA[:,1], vertA[:,2], faceA, representation='wireframe') 
    elif kind in ["Bool",
                "ScalarArea",
                "AreaNormal",
                "QuadForm",
                "VertexAngularDefect",
                "EdgeAngularDefect"]:  
        mode = None
        features = np.array(kwargs['features'])
        x = kwargs['x']
        y = kwargs['y']
        z = kwargs['z']
        assert len(x) == len(features)  
        N = len(features)
        scalars = np.arange(N) # Key point: set an integer for each point
        colors = np.zeros((N, 4), dtype=np.uint8)        
        colors[:,-1] = 255 # No transparency
        
        if kind == 'Bool':
            colors[:,0] = 0        
            colors[:,1] = 255
            colors[:,2] = 0            
            pts = mlab.quiver3d(x-spatialSize/2, y-spatialSize/2+0.5, z-spatialSize/2+0.5, 
                            np.ones(N), np.zeros(N), np.zeros(N), 
                            scalars=scalars, mode='cube', scale_factor=0.7, line_width=10) 
        elif kind == 'ScalarArea':
            features = features.ravel()
            colors[:,2] = 255
            colors[:,1] = (255*(1-features/np.max(features))).astype(np.uint8)
            colors[:,0] = (255*(1-features/np.max(features))).astype(np.uint8)       
            pts = mlab.quiver3d(x-spatialSize/2, y-spatialSize/2+0.5, z-spatialSize/2+0.5, 
                            np.ones(N), np.zeros(N), np.zeros(N), 
                            scalars=scalars, mode='cube', scale_factor=0.7, line_width=10) 
        elif kind == 'AreaNormal':
            colors[:,2] = 255
            colors[:,1] = 0
            colors[:,0] = 0     
            pts = mlab.quiver3d(x-spatialSize/2+0.5, y-spatialSize/2+0.5, z-spatialSize/2+0.5, 
                        -features[:,0], -features[:,1], -features[:,2], 
                        scalars=scalars, mode='arrow', scale_factor=1.9, line_width=10) 
        elif kind == 'VertexAngularDefect':
            features = features.ravel()
            th = np.pi
            colors[:,0] = (255*(1+np.maximum(-1, np.clip(features, -th, 0)/th))).astype(np.uint8)
            colors[:,1] = (255*(1-np.minimum(1, np.clip(features, 0, th)/th)+
                               np.maximum(-1, np.clip(features, -th, 0)/th))).astype(np.uint8)
            colors[:,2] = (255*(1-np.minimum(1, np.clip(features, 0, th)/th))).astype(np.uint8)      
            pts = mlab.quiver3d(x-spatialSize/2, y-spatialSize/2+0.5, z-spatialSize/2+0.5, 
                        np.ones(N), np.zeros(N), np.zeros(N), 
                        scalars=scalars, mode='cube', scale_factor=0.7, line_width=10)  
        elif kind == 'EdgeAngularDefect':
            features = features.ravel()
            th = np.pi
            colors[:,0] = (255*(1+np.maximum(-1, np.clip(features, -th, 0)/th))).astype(np.uint8)
            colors[:,1] = (255*(1-np.minimum(1, np.clip(features, 0, th)/th)+
                               np.maximum(-1, np.clip(features, -th, 0)/th))).astype(np.uint8)
            colors[:,2] = (255*(1-np.minimum(1, np.clip(features, 0, th)/th))).astype(np.uint8)      
            pts = mlab.quiver3d(x-spatialSize/2, y-spatialSize/2+0.5, z-spatialSize/2+0.5, 
                        np.ones(N), np.zeros(N), np.zeros(N), 
                        scalars=scalars, mode='cube', scale_factor=0.7, line_width=10)  
        elif kind == 'QuadForm':
            mode = 'custom'
            r = 0.5
            phi, theta = np.mgrid[0:np.pi:11j, 0:2*np.pi:11j]
            XYZ = r*np.concatenate([(np.sin(phi)*np.cos(theta)).reshape((1, phi.shape[0], -1)),
                                    (np.sin(phi)*np.sin(theta)).reshape((1, phi.shape[0], -1)),
                                     np.cos(phi).reshape((1, phi.shape[0], -1))], axis=0)
            
            for n in range(N):
                Q = np.array([[features[n,0], features[n,3], features[n,4]],
                              [features[n,3], features[n,1], features[n,5]],
                              [features[n,4], features[n,5], features[n,2]]])
                Q = np.trace(Q)*np.eye(3)-Q+1e-3*np.eye(3)
                                              
                XYZ1 = np.tensordot(linalg.sqrtm(Q), XYZ, axes=(1,0))
                mlab.mesh(x[n]-spatialSize/2+0.5+XYZ1[0], 
                          y[n]-spatialSize/2+0.5+XYZ1[1], 
                          z[n]-spatialSize/2+0.5+XYZ1[2], color=(1,0,0)) 
        else:
            raise NotImplementedError         

        if mode != 'custom':
            pts.glyph.color_mode = 'color_by_scalar' 
            try:
                pts.module_manager.scalar_lut_manager.lut.table = colors 
            except:
                pass                              
        mlab.draw() 
    if title:
        mlab.title(kind, color=(0,0,0), size=0.7, height=0.75)
    
    if save:
        mlab.savefig('pics/'+kind+'.png')    
          
    return f


def main(spatialSize=24, 
         dataset='ESB', 
         case='Solid Of Revolution/90 degree elbows/1309429', 
         passMeshOrPath='mesh', 
         randRotate=True):
    ''' For a given surface, show voxelization based on surface area, and standard Mayavi views. '''        
    
    if dataset == 'ModelNet':
        rootFolder = '../datasets/ModelNet10'        
        if case == 'random':  
            labelL = [item for item in os.listdir(rootFolder) if os.path.isdir(os.path.join(rootFolder, item))]      
            label = labelL[np.random.randint(len(labelL))]
            modelL = os.listdir(os.path.join(rootFolder,label,'train'))
            model = modelL[np.random.randint(len(modelL))]
            print 'Model:', model
            modelpath = os.path.join(rootFolder,label,'train',model)
        else: # e.g., stairs_0067, flower_pot_0148
            print 'Model:', case 
            modelClass = case[:-5]            
            modelpath = os.path.join(rootFolder, modelClass, 'train', case+'.off')
            print modelpath
        
        vertA0, faceA = vf.getDataOff(modelpath)  
        
    elif dataset == 'ESB': 
        rootFolder = '../datasets/ESB'        
        if case == 'random':  
            F0 = [f for f in os.listdir(rootFolder) if os.path.isdir(os.path.join(rootFolder, f))]
            assert len(F0) == 3
            n0 = np.random.randint(3)
            
            F1 = [f for f in os.listdir(os.path.join(rootFolder, F0[n0])) 
                  if os.path.isdir(os.path.join(rootFolder, F0[n0], f))]
            n1 = np.random.randint(len(F1))
            
            modelL = [f for f in os.listdir(os.path.join(rootFolder, F0[n0], F1[n1])) 
                  if f.endswith('.off')]
            n2 = np.random.randint(len(modelL))
            model = modelL[n2]
            print 'Model: %s/%s/%s' %(F0[n0], F1[n1], model[:-4])

            modelpath = os.path.join(rootFolder, F0[n0], F1[n1], model)
        else: 
            print 'Model:', case         
            modelpath = os.path.join(rootFolder, case+'.off')
            print modelpath
        
        vertA0, faceA = vf.getDataOff(modelpath)            
    
    elif dataset == 'custom':
        if case == 'cube':    
            vertA0 = np.zeros((2,2,2,3))
            vertA0[1,:,:,0] = 1.
            vertA0[:,1,:,1] = 1.
            vertA0[:,:,1,2] = 1.
            vertA0 = vertA0.reshape((8,3))
            
            faceA = np.zeros((12,3), dtype='int')
            n = 0
            for i in range(8):
                for j in range(i):
                    for k in range(j):
                        if ((np.linalg.norm(vertA0[i]-vertA0[j])+
                            np.linalg.norm(vertA0[i]-vertA0[k])+
                            np.linalg.norm(vertA0[j]-vertA0[k])) < 3.5 
                            and int(np.sum(vertA0[i]+vertA0[j]+vertA0[k]))%2 == 0):
                                faceA[n] = np.array([i, j, k])
                                n += 1
                                
        elif case == 'triangle':
            vertA0 = np.array([[0,0,0],[0,0,1],[0,1,0],[1,0,0]], dtype='float64')
            faceA = np.array([[0,1,2]], dtype='int64')
        else:
            raise NotImplementedError

    if randRotate:
        assert passMeshOrPath == 'mesh', NotImplementedError
        vertA0 = transforms.randRot(vertA0, 10.)
    
    print 'Number of vertices:', len(vertA0)
    print 'Number of faces:', len(faceA)  
  
    vertA0 = transforms.fitToCube(vertA0, spatialSize, faceA=faceA, mode='scaleShift')
        
    plotShape('solid', vertA=vertA0, faceA=faceA, spatialSize=spatialSize)
    plotShape('wireframe', vertA=vertA0, faceA=faceA, spatialSize=spatialSize)
    
    for nFeat, feat in enumerate(["Bool", 
                                  "ScalarArea", 
                                  "AreaNormal", 
                                  "VertexAngularDefect", 
                                  "QuadForm",
                                  "EdgeAngularDefect",                                
                                  ]):
        print '=============', feat
        t0 = time.time()
        features, x, y, z, nFeatPerVoxel, nSpatialSites = vf.getVoxelFeatures(vertA0, faceA, spatialSize, 
                            set([feat]), 0)
        t1 = time.time()
        print 'Time:', t1-t0    
        print 'Features per voxel:', nFeatPerVoxel

        if nFeat == 0:
            x0 = np.copy(x)
            y0 = np.copy(y)
            z0 = np.copy(z)
            nNonempty = nSpatialSites
            share = float(nSpatialSites)/(spatialSize*spatialSize*spatialSize) 
            print 'Number of nonempty voxels:', nNonempty
            print 'Share of non-empty voxels:', share                
        else:
            assert np.sum(np.abs(x-x0)+np.abs(y-y0)+np.abs(z-z0)) == 0
            assert nNonempty == nSpatialSites
            assert share == float(nSpatialSites)/(spatialSize*spatialSize*spatialSize)
                    
        plotShape(feat, features=features, x=x, y=y, z=z, spatialSize=spatialSize)
           
    mlab.show()
    

if __name__ == '__main__':
    main()    
