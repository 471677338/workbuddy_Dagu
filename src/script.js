/**
 * =============================================================================
 * Three.js Journey — 第 12 课: 3D Text（3D 文字）
 * =============================================================================
 *
 * 课程内容:
 *   1. 字体准备 (typeface JSON 格式)
 *   2. FontLoader + TextGeometry (3D 文字几何体)
 *   3. 居中文字 (boundingBox / center())
 *   4. Matcap 材质
 *   5. 100 个甜甜圈漂浮环绕
 *   6. 性能优化 (复用几何体和材质)
 *
 * 参考: ilithya 的 portfolio https://www.ilithya.rocks/
 *
 * =============================================================================
 */

import * as THREE from 'three'
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js'
import { FontLoader } from 'three/examples/jsm/loaders/FontLoader.js'
import { TextGeometry } from 'three/examples/jsm/geometries/TextGeometry.js'

// Canvas
const canvas = document.querySelector('canvas.webgl')

// Scene
const scene = new THREE.Scene()

// =============================================================================
// Textures
// =============================================================================

const textureLoader = new THREE.TextureLoader()
const matcapTexture = textureLoader.load('/textures/matcaps/1.png')
matcapTexture.colorSpace = THREE.SRGBColorSpace

// =============================================================================
// Fonts — 字体文件加载 (异步)
// =============================================================================
//
// 字体必须是 typeface JSON 格式:
//   从 node_modules/three/examples/fonts/ 复制
//   或用在线工具 https://gero3.github.io/facetype.js/ 转换
//
// FontLoader 的工作方式和 TextureLoader 类似,
// 但后续代码必须写在加载成功的回调函数里
//
// =============================================================================

const fontLoader = new FontLoader()

fontLoader.load(
    '/fonts/helvetiker_regular.typeface.json',
    (font) =>
    {
        console.log('font loaded')

        // ============================================================
        // TextGeometry — 创建 3D 文字
        // ============================================================
        //
        // 参数:
        //   text          — 要显示的文字
        //   font          — FontLoader 加载好的字体对象
        //   size          — 文字大小
        //   depth         — 文字的厚度 (Z 轴深度)
        //   curveSegments — 曲线细分, 值越大越平滑但越耗性能
        //   bevelEnabled  — 是否启用倒角
        //   bevelThickness— 倒角厚度
        //   bevelSize     — 倒角大小
        //   bevelOffset   — 倒角偏移
        //   bevelSegments — 倒角细分
        //
        const textGeometry = new TextGeometry(
            'Hello Three.js',
            {
                font: font,
                size: 0.5,
                depth: 0.2,
                curveSegments: 12,
                bevelEnabled: true,
                bevelThickness: 0.03,
                bevelSize: 0.02,
                bevelOffset: 0,
                bevelSegments: 5
            }
        )

        // ============================================================
        // 居中文字
        // ============================================================
        //
        // 方法 1: 手动计算 boundingBox 并平移 (了解原理)
        //   textGeometry.computeBoundingBox()
        //   textGeometry.translate(
        //       - (textGeometry.boundingBox.max.x - 0.02) * 0.5,
        //       - (textGeometry.boundingBox.max.y - 0.02) * 0.5,
        //       - (textGeometry.boundingBox.max.z - 0.03) * 0.5
        //   )
        //
        // 方法 2: 直接用 center() — 更简洁 (推荐)
        textGeometry.center()

        // ============================================================
        // 材质 (Matcap)
        // ============================================================

        const material = new THREE.MeshMatcapMaterial({ matcap: matcapTexture })

        // 文字网格
        const text = new THREE.Mesh(textGeometry, material)
        scene.add(text)

        // ============================================================
        // 添加 100 个甜甜圈漂浮环绕
        // ============================================================
        //
        // 优化: 几何体和材质提到循环外面, 复用实例
        //
        const donutGeometry = new THREE.TorusGeometry(0.3, 0.2, 20, 45)

        for (let i = 0; i < 100; i++)
        {
            const donut = new THREE.Mesh(donutGeometry, material)

            // 随机位置 (-5 ~ 5)
            donut.position.x = (Math.random() - 0.5) * 10
            donut.position.y = (Math.random() - 0.5) * 10
            donut.position.z = (Math.random() - 0.5) * 10

            // 随机旋转 (0 ~ PI)
            donut.rotation.x = Math.random() * Math.PI
            donut.rotation.y = Math.random() * Math.PI

            // 随机缩放 (统一值)
            const scale = Math.random()
            donut.scale.set(scale, scale, scale)

            scene.add(donut)
        }
    }
)

// =============================================================================
// Sizes, Camera, Renderer, Controls
// =============================================================================

const sizes = {
    width: window.innerWidth,
    height: window.innerHeight
}

const camera = new THREE.PerspectiveCamera(75, sizes.width / sizes.height, 0.1, 100)
camera.position.set(1, 1, 2)
scene.add(camera)

const renderer = new THREE.WebGLRenderer({ canvas: canvas })
renderer.setSize(sizes.width, sizes.height)
renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2))

const controls = new OrbitControls(camera, canvas)
controls.enableDamping = true

window.addEventListener('resize', () =>
{
    sizes.width = window.innerWidth
    sizes.height = window.innerHeight
    camera.aspect = sizes.width / sizes.height
    camera.updateProjectionMatrix()
    renderer.setSize(sizes.width, sizes.height)
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2))
})

// Tick
const tick = () =>
{
    controls.update()
    renderer.render(scene, camera)
    window.requestAnimationFrame(tick)
}

tick()
