/**
 * @license
 * Cesium - https://github.com/CesiumGS/cesium
 * Version 1.114
 *
 * Copyright 2011-2022 Cesium Contributors
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 * http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 *
 * Columbus View (Pat. Pend.)
 *
 * Portions licensed separately.
 * See https://github.com/CesiumGS/cesium/blob/main/LICENSE.md for full licensing details.
 */
import{a as T}from"./chunk-S52AQ5GZ.js";import"./chunk-T5LTBJR6.js";import{a as f}from"./chunk-WJWQTD3N.js";import"./chunk-L4VLY3HN.js";import{a as G}from"./chunk-D4BCVU35.js";import{a as C}from"./chunk-C5E6OQHH.js";import"./chunk-4BEUQXNB.js";import"./chunk-N4LA2RYW.js";import"./chunk-LGDGOZBO.js";import"./chunk-KVLKTV7L.js";import"./chunk-42WKPM5N.js";import{a as L}from"./chunk-SXCE2VWF.js";import"./chunk-NLCQYVEX.js";import"./chunk-ZWKNWN2X.js";import"./chunk-JXYWMXB6.js";import{a as w}from"./chunk-PDIF2AUE.js";import{a as O}from"./chunk-LIAARPDW.js";import{b,c as d,d as k}from"./chunk-PRRW7QSP.js";import{d as P}from"./chunk-4NBDOIVA.js";import"./chunk-YIJHUUZY.js";import"./chunk-CSZ6CHXI.js";import{a as H}from"./chunk-XXK6IR5Y.js";import{a as l,d as g}from"./chunk-IGBMENRT.js";import"./chunk-SEE54P6A.js";import"./chunk-JNX2URIY.js";import"./chunk-4Z3GDVJK.js";import{a as c}from"./chunk-LU3FCBPP.js";import{b as a}from"./chunk-S2577PU4.js";import{e as u}from"./chunk-2TPVVSVW.js";function E(e){let r=e.length,t=new Float64Array(3*r),o=w.createTypedArray(r,2*r),n=0,i=0;for(let a=0;a<r;a++){let s=e[a];t[n++]=s.x,t[n++]=s.y,t[n++]=s.z,o[i++]=a,o[i++]=(a+1)%r}let s=new O({position:new k({componentDatatype:H.DOUBLE,componentsPerAttribute:3,values:t})});return new d({attributes:s,indices:o,primitiveType:b.LINES})}function m(e){e=c(e,c.EMPTY_OBJECT);let r=e.polygonHierarchy;a.defined("options.polygonHierarchy",r),this._polygonHierarchy=r,this._workerName="createCoplanarPolygonOutlineGeometry",this.packedLength=f.computeHierarchyPackedLength(r,l)+1}m.fromPositions=function(e){e=c(e,c.EMPTY_OBJECT),a.defined("options.positions",e.positions);let r={polygonHierarchy:{positions:e.positions}};return new m(r)},m.pack=function(e,r,t){return a.typeOf.object("value",e),a.defined("array",r),t=c(t,0),t=f.packPolygonHierarchy(e._polygonHierarchy,r,t,l),r[t]=e.packedLength,r};var v={polygonHierarchy:{}};m.unpack=function(e,r,t){a.defined("array",e),r=c(r,0);let o=f.unpackPolygonHierarchy(e,r,l);r=o.startingIndex,delete o.startingIndex;let n=e[r];return u(t)||(t=new m(v)),t._polygonHierarchy=o,t.packedLength=n,t},m.createGeometry=function(e){let r=e._polygonHierarchy,t=r.positions;if(t=L(t,l.equalsEpsilon,!0),t.length<3||!T.validOutline(t))return;let o=f.polygonOutlinesFromHierarchy(r,!1);if(0===o.length)return;let n=[];for(let a=0;a<o.length;a++){let e=new G({geometry:E(o[a])});n.push(e)}let i=C.combineInstances(n)[0],s=P.fromPoints(r.positions);return new d({attributes:i.attributes,indices:i.indices,primitiveType:i.primitiveType,boundingSphere:s})};var h=m;function A(e,r){return u(r)&&(e=h.unpack(e,r)),e._ellipsoid=g.clone(e._ellipsoid),h.createGeometry(e)}var Z=A;export{Z as default};