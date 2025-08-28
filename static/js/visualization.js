// /static/js/visualization.js

import * as THREE from 'three';
import { OrbitControls } from 'OrbitControls';
import { BVHLoader } from 'BVHLoader';

'use strict';

const scenes = [];
let animationMixers = [];
const clock = new THREE.Clock();

// --- You can easily change the thickness and colors here! ---
const BONE_THICKNESS = 0.01;
const JOINT_SIZE = 0.02;

const boneMaterial = new THREE.MeshStandardMaterial({
    color: 0x444444,
    roughness: 0.5,
    metalness: 0.2
});

const jointMaterial = new THREE.MeshStandardMaterial({
    color: 0x007bff,
    roughness: 0.4,
    metalness: 0.1
});
// -----------------------------------------------------------------

function createMeshesForSkeleton(bone) {
    const jointSphere = new THREE.SphereGeometry(JOINT_SIZE, 16, 16);
    const jointMesh = new THREE.Mesh(jointSphere, jointMaterial);
    bone.add(jointMesh);

    bone.children.forEach((child) => {
        if (child.isBone) {
            const boneVector = child.position;
            const boneLength = boneVector.length();

            if (boneLength > 0.001) {
                const boneCylinder = new THREE.CylinderGeometry(BONE_THICKNESS, BONE_THICKNESS, boneLength, 8);
                const boneMesh = new THREE.Mesh(boneCylinder, boneMaterial);
                boneMesh.position.copy(boneVector).multiplyScalar(0.5);

                const startVec = new THREE.Vector3(0, 1, 0);
                const endVec = boneVector.clone().normalize();
                
                const quaternion = new THREE.Quaternion();
                quaternion.setFromUnitVectors(startVec, endVec);
                boneMesh.quaternion.copy(quaternion);

                bone.add(boneMesh);
            }
            
            createMeshesForSkeleton(child);
        }
    });
}


function setupViewer(container, modNo) { // <-- NEW: We're passing in modNo
    const bvhFile = container.dataset.bvhFile;
    if (!bvhFile) {
        console.error("No BVH file specified for viewer:", container.id);
        return;
    }

    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0xeeeeee);
    
    // --- NEW: Camera Configuration based on modNo ---
    const camera = new THREE.PerspectiveCamera(60, container.clientWidth / container.clientHeight, 1, 2000);
    
    // Default camera settings
    let cameraPos = new THREE.Vector3(0, 150, 400); // Default frontal view
    let cameraTarget = new THREE.Vector3(0, 75, 0);   // Default target is the character's torso

    // --- Customize camera positions for each mod_no (the index of the animation pair) ---
    // Remember, mod_no is a zero-based index (0, 1, 2, ...)
    switch (modNo) {
        case 0: // For the first pair in any category list
            // Example: A high-angle view
            cameraPos.set(-125, 150, 350);
            cameraTarget.set(-50, 75, 50);
            break;
        case 1: // For the second pair in any category list
            // Example: A standard frontal view
            cameraPos.set(20, 130, 150);
            break;
        case 2: // For the third pair in any category list
            // Example: A side view
            cameraPos.set(150, 150, 50);
            break;
        case 3: // For the fourth pair in any category list
            // Example: A low-angle view
            cameraPos.set(20, 130, 150);
            break;
        default:
            // Uses the default cameraPos defined above for any other mod_no
            break;
    }
    camera.position.copy(cameraPos);
    // --- END of new camera configuration ---

    const renderer = new THREE.WebGLRenderer({ antias: true });
    renderer.setSize(container.clientWidth, container.clientHeight);
    container.appendChild(renderer.domElement);
    
    const controls = new OrbitControls(camera, renderer.domElement);
    controls.target.copy(cameraTarget); // Set where the camera initially looks
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
        const skeletonRoot = result.skeleton.bones[0];
        createMeshesForSkeleton(skeletonRoot);

        const characterContainer = new THREE.Group();
        characterContainer.add(skeletonRoot);

        characterContainer.updateMatrixWorld(true); 
        const box = new THREE.Box3().setFromObject(characterContainer);
        const size = new THREE.Vector3();
        box.getSize(size);
        
        if (size.y > 0) {
            const desiredHeight = 150;
            const scaleFactor = desiredHeight / size.y;
            characterContainer.scale.set(scaleFactor, scaleFactor, scaleFactor);
            
            const postScaleBox = new THREE.Box3().setFromObject(characterContainer);
            const postScaleCenter = new THREE.Vector3();
            postScaleBox.getCenter(postScaleCenter);
            characterContainer.position.sub(postScaleCenter);
        }

        scene.add(characterContainer);

        scenes.push({
            renderer,
            scene,
            camera,
            controls,
        });

        const mixer = new THREE.AnimationMixer(characterContainer);
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

// --- NEW: Read mod_no from the data attribute ---
const viewerContainer = document.querySelector('.viewer-container');
const modNo = viewerContainer ? parseInt(viewerContainer.dataset.modNo, 10) : -1; // .dataset.modNo corresponds to data-mod-no

if (viewerLeft && viewerRight) {
    setTimeout(() => {
        // Pass the mod_no to each viewer setup
        setupViewer(viewerLeft, modNo);
        setupViewer(viewerRight, modNo);
        animate();
    }, 100);
}