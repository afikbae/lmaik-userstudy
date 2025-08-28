// /static/js/visualization.js

import * as THREE from 'three';
import { OrbitControls } from 'OrbitControls';
import { BVHLoader } from 'BVHLoader';

'use strict';

const scenes = [];
let animationMixers = [];
const clock = new THREE.Clock();

function setupViewer(container) {
    const bvhFile = container.dataset.bvhFile;
    if (!bvhFile) {
        console.error("No BVH file specified for viewer:", container.id);
        return;
    }

    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0xeeeeee);

    const camera = new THREE.PerspectiveCamera(60, container.clientWidth / container.clientHeight, 1, 2000);
    camera.position.set(0, 150, 400);

    const renderer = new THREE.WebGLRenderer({ antialias: true });
    renderer.setSize(container.clientWidth, container.clientHeight);
    container.appendChild(renderer.domElement);
    
    const controls = new OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    controls.dampingFactor = 0.05;

    const ambientLight = new THREE.AmbientLight(0xffffff, 0.8);
    scene.add(ambientLight);
    const directionalLight = new THREE.DirectionalLight(0xffffff, 1.0);
    directionalLight.position.set(0, 1, 0.5).normalize();
    scene.add(directionalLight);
    
    const gridHelper = new THREE.GridHelper(800, 20);
    scene.add(gridHelper);

    const loader = new BVHLoader();
    loader.load(bvhFile, function (result) {
        const skeletonHelper = new THREE.SkeletonHelper(result.skeleton.bones[0]);
        skeletonHelper.skeleton = result.skeleton;
        scene.add(skeletonHelper);

        const boneContainer = new THREE.Group();
        boneContainer.add(result.skeleton.bones[0]);
        scene.add(boneContainer);

        // --- Auto-scaling ---
        const box = new THREE.Box3();
        result.skeleton.bones[0].updateWorldMatrix(true, true);
        for (const bone of result.skeleton.bones) {
            const bonePos = new THREE.Vector3();
            bone.getWorldPosition(bonePos);
            box.expandByPoint(bonePos);
        }
        const size = new THREE.Vector3();
        box.getSize(size);
        const center = new THREE.Vector3();
        box.getCenter(center);
        if (size.x !== 0 || size.y !== 0 || size.z !== 0) {
            const desiredSize = 150;
            const maxSize = Math.max(size.x, size.y, size.z);
            let scaleFactor = 1;
            if (maxSize > 0 && isFinite(maxSize)) {
                scaleFactor = desiredSize / maxSize;
            }
            boneContainer.scale.set(scaleFactor, scaleFactor, scaleFactor);
            const scaledCenterOffset = new THREE.Vector3().copy(center).multiplyScalar(scaleFactor);
            boneContainer.position.sub(scaledCenterOffset);
        }

        scenes.push({
            renderer,
            scene,
            camera,
            controls,
        });

        const mixer = new THREE.AnimationMixer(result.skeleton.bones[0]);
        mixer.clipAction(result.clip).setEffectiveWeight(1.0).play();
        animationMixers.push(mixer);
    });

    window.addEventListener('resize', () => {
        camera.aspect = container.clientWidth / container.clientHeight;
        camera.updateProjectionMatrix();
        renderer.setSize(container.clientWidth, container.clientHeight);
    }, false);
}

function animate() {
    requestAnimationFrame(animate);
    const delta = clock.getDelta();

    if (animationMixers.length > 0) {
        animationMixers.forEach(mixer => mixer.update(delta));
    }
    
    scenes.forEach(s => {
        s.controls.update();
        s.renderer.render(s.scene, s.camera);
    });
}

// --- Initialize ---
const viewerLeft = document.getElementById('viewer-left');
const viewerRight = document.getElementById('viewer-right');

if (viewerLeft && viewerRight) {
    setupViewer(viewerLeft);
    setupViewer(viewerRight);
    animate();
}