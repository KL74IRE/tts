"""
CS426 Episode 8 — Q&A Revision Podcast Generator
==================================================
Generates a single MP3 — a spoken Q&A revision session covering all
key concepts from Episodes 1 to 7.

Format:
    - Full spoken intro explaining what the podcast is
    - Question read aloud
    - 3-second silence (thinking gap)
    - Correct answer read twice
    - Short explanation of why it is correct
    - 1-second silence
    - Next question

Requirements:
    pip install edge-tts

Usage:
    python generate_cs426_ep8_qna.py

Output:
    audio/CS426_Episode8_QnA_Revision.mp3

Notes:
    - Requires internet connection — edge-tts connects to Microsoft Speech servers
    - Uses Emily (en-IE-EmilyNeural) — Irish female neural voice
    - Run from any folder — the audio subfolder is created automatically
"""

import edge_tts
import asyncio
import os
import re
import struct
import wave

# ── Config ────────────────────────────────────────────────────────────────────
OUTPUT_DIR  = "audio"
OUTPUT_FILE = "CS426_Episode8_QnA_Revision.mp3"
VOICE       = "en-IE-EmilyNeural"

# ── Content ───────────────────────────────────────────────────────────────────

INTRO = """
Welcome to the CS426 Computer Graphics Q and A Revision Podcast.
This is Episode 8 — your exam preparation session.

This podcast covers all key concepts from Episodes 1 through 7.
It includes rendering foundations, geometry and projection, illumination and colour,
rotation and orientation, simulation, displays and hardware, and code analysis.

Here is how this session works. I will read a question.
You will have 3 seconds to think of your answer.
Then I will read the correct answer twice, followed by a short explanation of why it is correct.
There will be a brief pause, then we move to the next question.

Try to answer out loud as if you are in the exam.
This will help you recall the material under pressure.

There are 40 questions in total.
If you can answer these confidently, you are well prepared for a first class result.

Let us begin.
"""

QNA = [

    # ── EPISODE 1: RENDERING FOUNDATIONS ──────────────────────────────────────

    {
        "q": "Question 1. What are the four ray types in a ray tracing system, and what does each one do?",
        "a": "The four ray types are: the primary or view ray, fired from the camera through each pixel into the scene to find the nearest intersection. The shadow ray, fired from the hit point toward each light source to determine if the point is in shadow. The reflection ray, fired at the mirror angle about the surface normal for shiny surfaces. And the refraction ray, bent according to Snell's Law when passing through transparent materials.",
        "why": "This is the most common opening question in every paper since 2010. All 25 papers ask about ray tracing. The four rays — primary, shadow, reflection, refraction — and the name Whitted 1979 are the key details. Snell's Law: n sub i times sine theta sub i equals n sub r times sine theta sub r."
    },
    {
        "q": "Question 2. Why do computer games use rasterisation instead of ray tracing?",
        "a": "Rasterisation projects triangles onto the screen in a highly regular, massively parallel operation that maps perfectly to GPU hardware. Every triangle is processed independently. Ray tracing has irregular memory access — rays can hit any object anywhere — plus recursion and per-ray branching, which are poorly suited to classic GPU pipelines. Nvidia RTX cards added dedicated ray tracing hardware in 2018.",
        "why": "This sub-question appears in most ray tracing questions. The key contrast is: rasterisation is regular and parallel — perfect for GPUs. Ray tracing is irregular and recursive — poorly suited to classic GPUs. RTX hardware changed this from 2018 onward."
    },
    {
        "q": "Question 3. Name the nine stages of the 3D rendering pipeline in execution order.",
        "a": "The nine stages in order are: World Transform, View Transform, Lighting, Projection, Back-face Culling, Frustum Clipping, Perspective Divide, Viewport Transform, and Rasterisation.",
        "why": "The pipeline appears in 24 of 25 papers. The order must be exact. A common mistake is placing Back-face Culling after Projection — it actually happens before or during Projection in most implementations. If asked for only 5 stages, combine them as: World, View plus Lighting, Projection, Clipping, Rasterisation."
    },
    {
        "q": "Question 4. What is the difference between a right-handed and left-handed coordinate system, and which software uses each?",
        "a": "In a right-handed system, pointing right-hand fingers along positive X and curling toward positive Y makes the thumb point along positive Z — out of the screen toward the viewer. Positive rotation is counter-clockwise from the positive axis end. Used by OpenGL, Blender, and XNA. In a left-handed system, the same gesture with the left hand makes positive Z go into the screen. Used by DirectX, POV-Ray, and Unity.",
        "why": "This appears in all 25 papers. The memory aid: OpenGL, Blender, XNA — right-handed, plus Z toward you. DirectX, POV-Ray, Unity — left-handed, plus Z away from you. The hand rule for rotation direction always comes up as a sub-question."
    },
    {
        "q": "Question 5. What is back-face culling, and how do you use dot and cross products to check if a polygon faces the camera?",
        "a": "Back-face culling discards triangles whose vertices appear in clockwise order from the camera — they are facing away. Counter-clockwise winding equals front face in OpenGL. To check: compute the surface normal N equals B minus A, cross product with C minus A. Compute the vector D from the camera position to the centroid. Compute the dot product d equals D dot N. If d is greater than zero, the polygon faces the camera and should be rendered. If d is less than or equal to zero, cull it.",
        "why": "Back-face culling appears in 18 papers. The cross product gives the normal. The dot product tests visibility. This specific two-step method — cross for normal, dot for camera test — is always the expected answer."
    },

    # ── EPISODE 2: GEOMETRY AND PROJECTION ────────────────────────────────────

    {
        "q": "Question 6. What is a homogeneous coordinate, and what does it mean when w equals zero?",
        "a": "A homogeneous coordinate represents a 3D point a, b, c as the 4D vector x, y, z, w where a equals x over w, b equals y over w, and c equals z over w. The component w is the scale factor. When w equals zero the coordinate represents a direction — a point at infinity — not a position. This is how parallel lines meet at a vanishing point in projective space.",
        "why": "Homogeneous coordinates appear in all 25 papers. The key facts: position has w equals 1, direction has w equals 0. All scalar multiples of a vector represent the same Euclidean point. The word homogeneous comes from the Greek homos meaning the same — all vectors along the same ray from the origin are the same point."
    },
    {
        "q": "Question 7. What are three key advantages of homogeneous coordinates over plain x, y, z coordinates?",
        "a": "First: translation can be expressed as matrix multiplication — this is impossible with 3 by 3 matrices. Second: perspective projection is a simple matrix multiply followed by dividing by w. Third: points at infinity — vanishing points — are handled without special cases in code.",
        "why": "This sub-question appears in many homogeneous coordinate questions. The translation advantage is the most important — it is the entire reason homogeneous coordinates are used in graphics pipelines. All three advantages should be stated when asked."
    },
    {
        "q": "Question 8. Write the 4 by 4 translation matrix for displacements dx, dy, dz, and the 4 by 4 scale matrix for sx, sy, sz.",
        "a": "The translation matrix is the identity matrix with dx, dy, dz placed in the rightmost column in rows 1, 2, and 3. The bottom row remains 0, 0, 0, 1. The scale matrix is a diagonal matrix with sx, sy, sz, and 1 on the diagonal, and zeros everywhere else.",
        "why": "All nine standard matrices appear in all 25 papers. The translation and scale matrices are the most straightforward. Common exam error: placing the translation values in the bottom row instead of the right column. The bottom row is 0, 0, 0, 1 always."
    },
    {
        "q": "Question 9. Derive the perspective projection formula using similar triangles. What does the bottom row of the matrix do?",
        "a": "Camera at origin, screen at distance d along Z. A 3D point P with coordinates X, Y, Z projects to screen point x, y. Similar triangles in the X direction give x over d equals X over Z, therefore x equals d times X over Z. Similarly y equals d times Y over Z. The matrix with rows 1 0 0 0, then 0 1 0 0, then 0 0 1 0, then 0 0 one-over-d 0, applied to X, Y, Z, 1 gives X, Y, Z, Z-over-d. After dividing by w equals Z-over-d: x equals dX over Z. The bottom row creates the perspective effect.",
        "why": "The perspective proof appears in 11 papers. The similar triangles argument is always expected. The key insight is that the bottom row of the matrix — 0, 0, one-over-d, 0 — is what puts Z into the w component, enabling the perspective divide that makes distant objects appear smaller."
    },
    {
        "q": "Question 10. Given vectors u equals (1, 2, 3) and v equals (minus 3, 0, 1), find the dot product and cross product. What does the dot product tell you?",
        "a": "Dot product: 1 times minus 3, plus 2 times 0, plus 3 times 1, equals minus 3 plus 0 plus 3, equals zero. The vectors are perpendicular. Cross product: i component is 2 times 1 minus 3 times 0 equals 2. j component is minus the quantity 1 times 1 minus 3 times minus 3, equals minus 10. k component is 1 times 0 minus 2 times minus 3, equals 6. Cross product is (2, minus 10, 6). Unit normal: magnitude is square root of 140, approximately 11.83. Unit normal is approximately (0.169, minus 0.845, 0.507).",
        "why": "These exact vectors appear in Summer 2024 Q1b and Summer 2025 Q1b — memorise this result. Dot product equals zero means perpendicular. The cross product gives the surface normal perpendicular to both vectors. The unit normal is required for Phong lighting calculations."
    },

    # ── EPISODE 3: ILLUMINATION AND COLOUR ────────────────────────────────────

    {
        "q": "Question 11. Write the Phong illumination equation and explain every term.",
        "a": "I equals k-a times I-A, plus I-I times the quantity k-d times L dot N, plus k-s times R dot V raised to the power n. k-a is the ambient coefficient, I-A is the ambient intensity. I-I is the incident point-source intensity. k-d is the diffuse coefficient, L is the unit vector toward the light, N is the unit surface normal. k-s is the specular coefficient, R is the reflection of L about N computed as 2 times L dot N times N minus L. V is the unit vector toward the viewer. n is the shininess exponent.",
        "why": "The Phong model appears in all 25 papers. The equation must be stated exactly, including all variables. Common error: forgetting to define R. R equals 2 times L dot N, times N, minus L. A larger n produces a smaller sharper highlight. n equals 100 is polished metal. n equals 2 is a whiteboard."
    },
    {
        "q": "Question 12. How do you identify ambient-only, diffuse-only, and specular lighting from images?",
        "a": "Ambient only: the image shows flat, uniform colour with no variation across the surface — no shading at all. Diffuse only: the image shows smooth shading that varies with the surface orientation relative to the light, but no bright concentrated spot. Specular present: there is a small, bright, concentrated highlight on the surface. Full Phong combines smooth shading across the whole surface with a bright highlight.",
        "why": "Image identification appears in almost every Phong question. The three keywords are: flat equals ambient, smooth shading equals diffuse, bright highlight equals specular. A Lambertian surface has k-s equals zero — equally bright from all viewing angles."
    },
    {
        "q": "Question 13. Convert RGB blue to CMY. Then convert CMY (1, 0, 1) back to RGB.",
        "a": "Blue in RGB is (0, 0, 1). Using C equals 1 minus R, M equals 1 minus G, Y equals 1 minus B: C equals 1 minus 0 equals 1, M equals 1 minus 0 equals 1, Y equals 1 minus 1 equals 0. CMY blue is (1, 1, 0) — cyan plus magenta. Converting CMY (1, 0, 1) to RGB: R equals 1 minus 1 equals 0, G equals 1 minus 0 equals 1, B equals 1 minus 1 equals 0. RGB is (0, 1, 0) which is green.",
        "why": "RGB to CMY conversion appears in 21 papers. The formula C equals 1 minus R, M equals 1 minus G, Y equals 1 minus B must be memorised in both directions. Summer 2024 asks exactly this CMY (1, 0, 1) to RGB conversion. The answer is green."
    },
    {
        "q": "Question 14. What happens when you mix magenta and yellow ink on white paper? Show the calculation.",
        "a": "Magenta ink absorbs green light. Yellow ink absorbs blue light. White paper reflects all — R, G, and B. Subtracting what is absorbed: (1,1,1) minus (0,1,0) minus (0,0,1) equals (1, 0, 0). The result is red. Magenta plus yellow gives red on white paper.",
        "why": "Subtractive mixing appears in many RGB-CMY questions. The key insight is that CMY inks absorb light — C absorbs red, M absorbs green, Y absorbs blue. The colour you see is what remains. Numerically: start with white (1,1,1), subtract what each ink absorbs."
    },
    {
        "q": "Question 15. What is the CIE chromaticity diagram, why are x and y sufficient to describe colour, and what is a metamer?",
        "a": "The CIE replaced RGB primaries with mathematical primaries X, Y, Z — all positive for every visible colour. Chromaticity values x equals X over X plus Y plus Z, y equals Y over X plus Y plus Z, z equals Z over X plus Y plus Z. Since x plus y plus z equals 1 always, knowing x and y determines z completely — colour is 2D. Plotting x, y for all monochromatic sources traces the horseshoe spectral locus. A metamer is two different spectra that produce the same x, y values and look identical to a human observer.",
        "why": "CIE appears in 13 papers. The 2D argument is the most common sub-question: x plus y plus z equals 1, so only 2 independent numbers describe colour. Y alone encodes brightness. The monitor gamut is the triangle formed by the RGB phosphor positions — colours outside cannot be reproduced."
    },

    # ── EPISODE 4: ROTATION AND ORIENTATION ───────────────────────────────────

    {
        "q": "Question 16. What are Euler angles, what is the line of nodes, and what is gimbal lock?",
        "a": "Euler angles describe any 3D orientation as three successive rotations: yaw about Z, then pitch about the new Y, then roll about the new X. The line of nodes is the intersection of the original XY plane and the rotated XY plane after yaw — it is the axis of the pitch rotation. Gimbal lock occurs when pitch reaches plus or minus 90 degrees — the yaw and roll axes become aligned and one degree of rotational freedom is lost. Yaw and roll produce the same motion. Orientation jumps when passing through 90 degrees of pitch.",
        "why": "Euler angles appear in 13 papers. The line of nodes is specifically asked in several. Gimbal lock is always asked as the flaw. The answer to gimbal lock is always quaternions — a single rotation about an arbitrary axis avoids sequential decomposition and therefore cannot lock."
    },
    {
        "q": "Question 17. Write the rotation quaternion for a 90 degree rotation about the Z axis, and explain the general form.",
        "a": "The general rotation quaternion for angle theta about unit axis u is: r equals cosine of theta over 2, comma, u-x times sine of theta over 2, comma, u-y times sine of theta over 2, comma, u-z times sine of theta over 2. For 90 degrees about Z: theta over 2 equals 45 degrees. u equals (0, 0, 1). r equals cosine 45, 0, 0, sine 45, which is approximately 0.707, 0, 0, 0.707.",
        "why": "Quaternion rotation form appears in 19 papers. The formula must be stated exactly. Common error: using theta instead of theta over 2 in the cosine and sine. To rotate a point p: express p as a pure quaternion (0, p-x, p-y, p-z), then compute r times p times r inverse, where r inverse equals the conjugate."
    },
    {
        "q": "Question 18. Compute the quaternion product (1 plus 2i plus 3j plus 0k) times (1 plus 0i plus j plus 2k).",
        "a": "Scalar: 1 times 1 minus 2 times 0 minus 3 times 1 minus 0 times 2 equals minus 2. i coefficient: 1 times 0 plus 2 times 1 plus 3 times 2 minus 0 times 1 equals 8. j coefficient: 1 times 1 minus 2 times 2 plus 3 times 1 plus 0 times 0 equals 0. k coefficient: 1 times 2 plus 2 times 1 minus 3 times 0 plus 0 times 1 equals 4. Result: minus 2 plus 8i plus 0j plus 4k.",
        "why": "This exact multiplication appears in multiple papers. The rules i squared equals j squared equals k squared equals ijk equals minus 1 must be applied carefully. Anti-commutative: ij equals k but ji equals minus k. jk equals i but kj equals minus i. ki equals j but ik equals minus j."
    },
    {
        "q": "Question 19. Name three facts about William Rowan Hamilton relevant to quaternions.",
        "a": "Hamilton was an Irish mathematician who lived from 1805 to 1865. He invented quaternions in 1843 while walking along the Royal Canal in Dublin. He was so excited by the discovery that he carved the fundamental formula — i squared equals j squared equals k squared equals ijk equals minus 1 — into the stone of Broom Bridge in Dublin. That bridge is now a historic landmark.",
        "why": "The Hamilton biography appeared in Summer 2025 Q3a — a new type of sub-question. Three facts are required: Irish nationality, 1843 Royal Canal discovery, Broom Bridge carving. Broom Bridge is also called Broome Bridge or Brougham Bridge in some sources."
    },
    {
        "q": "Question 20. Describe the arc-ball camera model and give the spherical coordinate formulas.",
        "a": "The arc-ball camera orbits a fixed target point at a fixed radius. Its position is described by spherical coordinates: longitude, latitude, and radius. The Cartesian position is: x equals radius times cosine of latitude times cosine of longitude. y equals radius times sine of latitude. z equals radius times cosine of latitude times sine of longitude. The camera always looks at the origin. When the absolute value of latitude exceeds 90 degrees, flip the camera up vector from (0, 1, 0) to (0, minus 1, 0) to prevent inversion.",
        "why": "Camera models appear in 15 papers. The arc-ball formula must be stated exactly. The latitude and longitude angles are in radians. The up vector flip is the fix for the gimbal-like inversion at the poles. First person is at the character's eye. Third person follows behind. Fly-through uses quaternion orientation updated each frame."
    },

    # ── EPISODE 5: SIMULATION ─────────────────────────────────────────────────

    {
        "q": "Question 21. How do you convert the second-order ODE m d squared x over dt squared equals minus kx into two first-order equations suitable for Euler's method?",
        "a": "Introduce velocity v equals dx over dt. The original equation becomes dv over dt equals minus k over m times x. The two first-order equations are: dv over dt equals minus k over m times x, and dx over dt equals v. The Euler iterating equations are: v new equals v old plus the quantity minus k over m times x, times dt. x new equals x old plus v old times dt. t new equals t old plus dt. Boundary conditions: x zero equals amplitude A, v zero equals zero, t zero equals zero.",
        "why": "Euler's method appears in 24 of 25 papers. The conversion from second-order to two first-order equations is always the first step. This specific equation is Simple Harmonic Motion — a spring. The pattern is always the same: introduce velocity, write two equations, iterate."
    },
    {
        "q": "Question 22. Write the Euler iterating equations for a 2D projectile with drag. State the boundary conditions.",
        "a": "Horizontal: vx new equals vx plus the quantity minus k over m times vx, times dt. x new equals x plus vx times dt. Vertical: vy new equals vy plus the quantity g minus k over m times vy, times dt. y new equals y plus vy times dt. t new equals t plus dt. Boundary conditions: x zero equals 0, vx zero equals initial horizontal launch speed such as 10 metres per second, y zero equals initial height H, vy zero equals 0.",
        "why": "The 2D projectile appears in many ODE questions. The key addition over SHM is the gravity term g in the vertical equation and the drag term in both. The bounce condition — when y is less than or equal to zero, set vy equals minus vy — is a common variation. Multiply by a restitution coefficient such as 0.8 for a damped bounce."
    },
    {
        "q": "Question 23. Explain double buffering and how it solves flickering. Name four callback functions and their triggers.",
        "a": "Single buffering draws directly into the visible frame buffer — the user sees the image being painted, causing flicker. Double buffering maintains a front buffer currently displayed, and a back buffer where rendering happens invisibly. When rendering is complete, glutSwapBuffers atomically swaps them. The user always sees a complete frame. Four callback functions: glutDisplayFunc triggers when the window needs redrawing. glutIdleFunc triggers when the CPU is idle and drives animation. glutKeyboardFunc triggers on ASCII key press. glutTimerFunc triggers after a specified delay in milliseconds for fixed-rate animation.",
        "why": "Double buffering appears in 24 of 25 papers. The answer must include both the front-back buffer explanation and at least three callback functions. The frame sequence is: idle fires update, update calls glutPostRedisplay, display fires draw, draw calls glutSwapBuffers. Single buffer is acceptable only for static scenes drawn once."
    },
    {
        "q": "Question 24. Define fractal and fractal dimension. Describe the Mandelbrot set algorithm.",
        "a": "A fractal is a self-similar shape where each part is approximately a reduced copy of the whole, with a non-integer fractal dimension D. Fractal dimension: L of lambda equals n times lambda to the power of 1 minus D. Plot log L against log lambda — the slope m equals 1 minus D, so D equals 1 minus m. Mandelbrot algorithm: for each pixel at position cx, cy in the complex plane, set a and b to zero. Iterate: store old a as at, then a new equals a squared minus b squared plus cx, b new equals 2 times at times b plus cy, increment counter g. Stop when root of a squared plus b squared reaches 2 or maximum iterations. Colour by escape count.",
        "why": "Fractals appear in 21 papers. The fractal dimension formula and the Mandelbrot iteration are both consistently tested. The Feigenbaum constant delta approximately 4.669 is the ratio of successive bifurcation spacings in the logistic map. Sierpinski gasket: three vertices, random point, move halfway to random vertex, plot, repeat 1 million times."
    },
    {
        "q": "Question 25. Describe the logistic map and what it reveals. What is the Feigenbaum constant?",
        "a": "The logistic map iterates r new equals b times r old times 1 minus r old. For each value of b from 1 to 4 in steps of about 0.005, start with r equals 0.5, iterate 100 times to settle, then plot the next 400 values of r against b. The plot reveals period-doubling bifurcations — at certain values of b the system doubles its period — eventually becoming chaotic. The Feigenbaum constant delta is approximately 4.669 and is the limiting ratio of successive distances between bifurcation points.",
        "why": "The logistic map appears in many fractal questions. The iteration formula must be stated exactly. The key insight is that period-doubling leads to chaos — a simple deterministic equation produces unpredictable behaviour. For the pendulum attractor: oval equals undamped periodic, inward spiral equals damped, closed loop equals limit cycle, complex shape equals strange attractor."
    },

    # ── EPISODE 6: DISPLAYS AND HARDWARE ──────────────────────────────────────

    {
        "q": "Question 26. Describe the cross-section of a TN LCD cell from back to front. Name all eight layers.",
        "a": "From back to front: LED backlight, rear linear polariser, rear glass substrate with ITO electrode and alignment ridges, the Twisted Nematic liquid crystal layer with a 90-degree molecular twist, front ITO electrode with alignment grooves at 90 degrees to the rear, front glass substrate, front linear polariser at 90 degrees to the rear polariser, and the colour filter — red, green, or blue — for each sub-pixel.",
        "why": "LCD construction appears in 14 papers. The eight layers must be given in order. ITO stands for Indium Tin Oxide — a transparent conductor. The two polarisers are crossed at 90 degrees to each other. Three sub-pixels per full-colour pixel."
    },
    {
        "q": "Question 27. Explain the OFF and ON states of a TN LCD pixel, and why the pixel must be driven with an AC signal.",
        "a": "OFF — no voltage: LC molecules follow the 90-degree twist. Backlight polarisation rotates 90 degrees through the LC layer and passes through the front polariser. Pixel is bright. ON — voltage applied: LC molecules align with the field, twist disappears, light polarisation does not rotate, blocked by front polariser. Pixel is dark. AC signal required: DC current causes electrolytic degradation — metal ions migrate and plate onto the ITO electrodes. An AC square wave creates the same optical effect without this damage. An XOR gate and oscillator generate the AC from a digital control signal.",
        "why": "The ON and OFF states and the AC signal reason appear in almost every LCD question. A common mistake is getting the ON and OFF states reversed — remember: voltage means dark, no voltage means bright. The AC reason is always the electrolytic damage to ITO."
    },
    {
        "q": "Question 28. Name the three types of inertial MoCap sensors, what each measures, and what a Kalman filter does.",
        "a": "Accelerometers measure linear acceleration along three axes. They use a MEMS proof mass on a spring — deflection proportional to acceleration, measured capacitively. They give pitch and roll from gravity direction but position drifts with double integration. Gyroscopes measure angular velocity using the MEMS Coriolis effect on a vibrating mass. Single integration gives orientation angle. Magnetometers measure Earth's magnetic field using magnetoresistive material — permalloy. They provide absolute yaw — compass heading — which accelerometers and gyroscopes alone cannot give. A Kalman filter fuses all three to produce stable low-drift estimates of yaw, pitch, and roll.",
        "why": "MoCap sensors appear in 6 papers. The three sensors have complementary roles: accelerometers give tilt, gyroscopes give rotation rate, magnetometers give compass heading. The Kalman filter is the standard fusion algorithm. Limitation: position drifts, yaw disturbed by magnetic interference, no absolute position reference."
    },
    {
        "q": "Question 29. Compare Kinect V1 structured light with Kinect V2 time-of-flight. Give the V2 depth formula.",
        "a": "Kinect V1 structured light: an IR projector emits a pseudo-random dot pattern. An IR camera images the dots on surfaces. A correlator compares each dot's observed position to its reference position. The disparity encodes depth — larger disparity means closer object. Kinect V2 time-of-flight: an IR source is amplitude-modulated at approximately 100 MHz. Each pixel has two sub-pixels Q1 and Q2 integrating charge during IR-on and IR-off phases. Depth z equals c over 2f, times Q2 divided by Q1 plus Q2, where c is the speed of light and f is the modulation frequency.",
        "why": "Kinect appears in 5 papers. Both versions must be described. The V2 depth formula must be stated with all terms defined. Both versions produce a depth map which is converted to a 3D point cloud, from which a skeletal body tracking algorithm identifies joint positions."
    },

    # ── EPISODE 7: CODE ANALYSIS ───────────────────────────────────────────────

    {
        "q": "Question 30. In a POV-Ray scene file, what do the camera block, light-source block, texture block, and clock variable do?",
        "a": "The camera block defines the viewpoint: location sets the camera position, look-at sets what it points at, and angle sets the field of view. The light-source block positions a light and sets its colour. The texture block inside an object sets its surface appearance: pigment sets the colour and finish sets the Phong parameters — ambient, diffuse, specular, and roughness. The clock variable runs from zero to one across all animation frames and is used to drive rotation or translation — for example rotate less-than 0, clock times 360, 0 greater-than produces one full Y-axis spin.",
        "why": "POV-Ray code appears in 17 papers, all from 2010 to 2019. The same four blocks appear in every scene. CSG operations: union combines, difference subtracts, intersection keeps shared volume. The dot-ini file sets Initial-Frame, Final-Frame, Initial-Clock, and Final-Clock."
    },
    {
        "q": "Question 31. What is the execution order of the six methods in an XNA Game1 class, and what happens in each?",
        "a": "The execution order is: Constructor, Initialize, LoadContent, then the Update and Draw loop repeating until exit, then UnloadContent. Constructor creates the GraphicsDeviceManager and sets Content.RootDirectory. Initialize does one-time game logic setup. LoadContent loads all textures and creates the SpriteBatch. Update runs at 60 Hz — reads keyboard input and updates positions. Draw clears the screen and renders everything using SpriteBatch.Begin, Draw calls, and End. UnloadContent releases resources on exit.",
        "why": "XNA code appears in 12 papers. The order must be exact: Constructor, Initialize, LoadContent, then Update-Draw loop. SpriteBatch batches 2D draw calls into one GPU operation. Magenta (R=255, G=0, B=255) is the colour key for transparency — pixels with that colour are made alpha zero when the texture is loaded."
    },
    {
        "q": "Question 32. In a Wavefront OBJ file, what do the lines beginning with v, vt, vn, and f represent? How do you identify a platonic solid?",
        "a": "v x y z defines a vertex position in 3D space. vt u v defines a texture coordinate in the range 0 to 1. vn x y z defines a vertex normal vector. f v1 slash t1 slash n1 v2 slash t2 slash n2 v3 slash t3 slash n3 defines a triangular face using one-based indices into the vertex, texture, and normal lists. To identify a platonic solid, count the f lines: 4 faces is a tetrahedron, 6 is a cube, 8 is an octahedron, 12 is a dodecahedron, 20 is an icosahedron.",
        "why": "Wavefront OBJ appears in 11 recent papers. The v, vt, vn, f prefixes must be known exactly. The MTL file is referenced by mtllib and materials are applied with usemtl. To add red triangles: add usemtl red-mat before the relevant f lines, then define red-mat in the MTL file with Kd 1.0 0.0 0.0."
    },
    {
        "q": "Question 33. In GLSL, what does the vertex shader do, what does the fragment shader do, and what is a uniform variable?",
        "a": "The vertex shader runs once per vertex. Its primary job is to transform the vertex position from model space to clip space using the MVP matrix: gl-Position equals MVP times vec4 of vertex position and 1.0. It also passes UV coordinates and normals to the rasteriser. The fragment shader runs once per rasterised pixel. It determines the final colour — typically by sampling a texture: color equals texture of sampler and UV dot rgba. A uniform variable is set by the CPU and is constant for all vertices and fragments in one draw call — for example the MVP matrix or a texture sampler.",
        "why": "GLSL appears in 8 recent papers. The vertex shader transforms — fragment shader colours. MVP equals Projection times View times Model. The four OpenGL libraries: OpenGL is the core GPU API, freeGLUT handles the window and events, GLEW loads extension functions, GLM provides the C++ math library."
    },
    {
        "q": "Question 34. How do you read a Blender Python animation script? What are the four steps?",
        "a": "Step 1: identify the primitive — look for primitive-uv-sphere-add, primitive-cylinder-add, or primitive-cone-add. Note the location and radius. Step 2: read the diffuse-color tuple — (1,0,0,1) is red, (0,0,1,1) is blue, (0,1,0,1) is green, (1,1,0,1) is yellow. Step 3: read the camera location and rotation-euler — rotation-euler (1.57, 0, 1.57) looks along minus Y from the plus X side. Step 4: trace the animation loop — for f in range, read the location formula. Circular orbit: x equals r cosine 2 pi f over N, y equals r sine 2 pi f over N. Sinusoidal: y equals math.sin of 4 pi times f over N. Linear: x equals f over 4.",
        "why": "Blender Python appears in 8 recent papers, all from 2021 onward. The exam always asks two things: describe the scene at frame zero, and describe the motion over the animation. State the starting position, colour, and path. Note how many complete orbits or oscillations occur over the full frame count."
    },

    # ── MIXED TOPICS: COMMON EXAM COMBINATIONS ─────────────────────────────────

    {
        "q": "Question 35. What is the Z-buffer, and what is the risk of setting zNear very small and zFar very large?",
        "a": "The Z-buffer is a 2D array the same size as the colour buffer that stores the depth of the nearest rendered fragment at each pixel. It is initialised to maximum depth each frame. For each rasterised fragment, if it is closer than the stored value, update both the colour buffer and the z-buffer. If further, discard. The risk of extreme near and far values: the z-buffer stores depth non-linearly — proportional to 1 over z. If zNear is near zero and zFar is very large, many different depths map to the same integer z value. Nearby surfaces at similar depths flicker — this is called z-fighting. Always tightly bracket the scene.",
        "why": "The z-buffer appears in 10 papers. The depth test in OpenGL: glEnable GL-DEPTH-TEST, clear with GL-DEPTH-BUFFER-BIT each frame. The z-fighting explanation — non-linear storage plus extreme near-far ratio causes precision loss — is always the expected answer for the risk question."
    },
    {
        "q": "Question 36. What is the pencil of planes, what is a vanishing point, and why does the horizon not move when the camera moves up or down?",
        "a": "A pencil of planes is a family of planes sharing a common line. In perspective geometry, all planes parallel to the ground plane share a line at infinity — the horizon. A vanishing point is where all parallel lines in the same 3D direction converge in the image — a homogeneous coordinate with w equals zero. The horizon does not move when the camera moves up or down because a vanishing point is determined only by direction. Moving the camera vertically does not change which direction the ground-plane lines point, so their vanishing points — and the horizon — stay fixed.",
        "why": "Pencil of planes appears in 9 recent papers. The horizon invariance proof is specifically asked in Autumn 2024 and Summer 2025. Drawing a tiled floor: horizon line, vanishing point, base divisions, lines to VP, diagonal to space the horizontal rows correctly."
    },
    {
        "q": "Question 37. Compare orthographic and perspective projection. When would you use each?",
        "a": "Perspective projection uses the matrix with 1-over-d in row 4 column 3. After dividing by w equals Z-over-d, objects further away appear smaller because x equals d times X over Z — distant objects have larger Z so appear smaller. Matches human vision. Used for 3D games, visualisation, and realistic rendering. Orthographic projection uses the matrix that drops Z entirely — row 3 column 3 is zero. No foreshortening — objects at different distances appear the same size. Used for technical drawing, CAD, engineering diagrams, and 2D games.",
        "why": "Both projections appear together in several papers. The key difference: perspective divides by Z causing foreshortening. Orthographic drops Z with no divide. In OpenGL: gluPerspective for perspective, gluOrtho2D for orthographic. Both are standard 4 by 4 matrices in the transformation pipeline."
    },
    {
        "q": "Question 38. Describe the rendering pipeline stage that happens just before rasterisation. What is the purpose of the perspective divide?",
        "a": "Just before rasterisation: the viewport transform maps normalised device coordinates to screen pixel coordinates using glViewport. Before that comes the perspective divide: each clip-space vertex stored as x, y, z, w is divided by w to produce normalised device coordinates in the cube from minus 1 to plus 1 in all three dimensions. The perspective divide is what creates the perspective effect — it divides the x and y screen coordinates by the depth Z, making distant objects appear smaller. Without it, the projection matrix alone produces no perspective.",
        "why": "The perspective divide is a specific stage often missed in pipeline questions. The NDC cube from minus 1 to plus 1 in all three dimensions is the output of the perspective divide. The viewport transform then maps this to the actual screen resolution."
    },
    {
        "q": "Question 39. What are the four reasons quaternions are preferred over Euler angles and rotation matrices for representing 3D orientation?",
        "a": "First: no gimbal lock — quaternions represent rotation as a single rotation about an arbitrary axis, never decomposing into three sequential rotations, so the lock condition cannot occur. Second: compact — only 4 numbers versus 9 for a rotation matrix. Third: easy smooth interpolation using SLERP — Spherical Linear Interpolation — between two orientations, producing smooth animation. Fourth: numerically stable — if floating-point drift occurs, a quaternion is easy to renormalise back to unit length.",
        "why": "The four advantages of quaternions appear in most quaternion questions. SLERP is important for animation — linearly interpolating Euler angles produces unnatural spinning. Renormalisation is simple: divide by the quaternion magnitude. Quaternion composition is one multiply: q total equals q1 times q2."
    },
    {
        "q": "Question 40. You are given a Blender Python script. The sphere is created at location (0,0,0) with diffuse-color (0, 0, 1, 1). The camera is at (0, minus 8, 0) with rotation-euler (1.57, 0, 0). The animation runs from frame 0 to 30. In the loop, a equals pi times p over 30.0, and sphere location equals (3 times cosine of a plus 3, 0, 3 times sine of a). Describe the scene at frame 0 and the motion.",
        "a": "At frame 0: p equals 0, a equals 0. Sphere location is (3 times cosine 0 plus 3, 0, 3 times sine 0) equals (3 plus 3, 0, 0) equals (6, 0, 0). The sphere is blue — diffuse-color (0, 0, 1, 1). The camera is at (0, minus 8, 0) with rotation-euler (1.57, 0, 0) — looking upward along plus Z from below. Over 31 frames, a increases from 0 to pi — a half circle. The sphere starts at (6, 0, 0), moves to (3, 0, 3) at frame 15 when a equals pi over 2, and ends at (0, 0, 0) at frame 30 when a equals pi. The sphere traces a half circle of radius 3 centred at (3, 0, 0) in the XZ plane.",
        "why": "This type of Blender script analysis appears in every paper from 2021 onward. Always evaluate frame 0 explicitly by substituting p equals 0 into the formula. Then evaluate the midpoint and endpoint. State the shape of the path, the radius, the centre, and the plane of motion. The colour tuple (0,0,1,1) is blue."
    },
]

OUTRO = """
That is the end of your CS426 Computer Graphics Q and A revision session.

You have covered 40 questions across all seven topic areas —
rendering foundations,
geometry and projection,
illumination and colour,
rotation and orientation,
simulation,
displays and hardware,
and code analysis.

Key formulas to have memorised before your exam:

Phong illumination: I equals k-a times I-A, plus I-I times bracket k-d times L dot N, plus k-s times R dot V to the power n.

Perspective projection: x equals d times X over Z, y equals d times Y over Z.

RGB to CMY: C equals 1 minus R, M equals 1 minus G, Y equals 1 minus B.

Rotation quaternion: r equals cosine theta over 2, comma, u times sine theta over 2.

Euler SHM: v new equals v old plus minus k over m times x, times dt. x new equals x old plus v old times dt.

Fractal dimension: slope of log L versus log lambda equals 1 minus D.

Mandelbrot iteration: a new equals a squared minus b squared plus cx. b new equals 2 times at times b plus cy.

Dot product: u dot v equals u-x v-x plus u-y v-y plus u-z v-z. Equals zero means perpendicular.

Cross product of (1,2,3) and (minus 3, 0, 1) equals (2, minus 10, 6). The vectors are perpendicular — dot product is zero.

Good luck in your exam. You have done the work. Now go prove it.
"""

# ── TTS helpers ───────────────────────────────────────────────────────────────

def clean(text):
    text = re.sub(r'  +', ' ', text)
    return text.strip()


# ── Progress bar (single-line, updates in place) ──────────────────────────────

class Progress:
    """Single-line progress bar that rewrites itself in place — no scroll spam."""

    def __init__(self, total, width=40):
        self.total   = total
        self.width   = width
        self.current = 0
        self.label   = ""

    def update(self, n=1, label=""):
        self.current += n
        if label:
            self.label = label
        self._draw()

    def set_label(self, label):
        self.label = label
        self._draw()

    def _draw(self):
        pct   = self.current / self.total if self.total else 1
        filled = int(self.width * pct)
        bar   = "█" * filled + "░" * (self.width - filled)
        line  = f"\r  [{bar}] {self.current}/{self.total}  {self.label:<45}"
        print(line, end="", flush=True)

    def done(self, msg="Complete"):
        bar = "█" * self.width
        print(f"\r  [{bar}] {self.total}/{self.total}  {msg:<45}", flush=True)


# ── TTS with retry ────────────────────────────────────────────────────────────

async def speak_to_file(text, path, retries=4, base_delay=2.0):
    """TTS with exponential-backoff retry — edge-tts rate-limits under load."""
    for attempt in range(retries):
        try:
            communicate = edge_tts.Communicate(text=clean(text), voice=VOICE)
            await communicate.save(path)
            return
        except Exception as e:
            if attempt < retries - 1:
                wait = base_delay * (2 ** attempt)   # 2s, 4s, 8s
                await asyncio.sleep(wait)
            else:
                raise


def silence_to_file(seconds, path):
    """Generate a silent audio file using pure Python — no API call needed."""
    sample_rate = 44100
    num_samples = int(sample_rate * seconds)
    wav_path    = path.replace('.mp3', '.wav')
    with wave.open(wav_path, 'w') as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(struct.pack('<' + 'h' * num_samples, *([0] * num_samples)))
    os.rename(wav_path, path)


def concat_mp3s(paths, output_path):
    """Concatenate MP3 files by binary concatenation."""
    with open(output_path, 'wb') as out:
        for p in paths:
            if os.path.exists(p) and os.path.getsize(p) > 0:
                with open(p, 'rb') as f:
                    out.write(f.read())


async def generate_question_block(i, item, tmp_dir, progress):
    """Generate all 4 audio segments for one question, update progress bar."""
    def tmp(name):
        return os.path.join(tmp_dir, name)

    q_path   = tmp(f"q{i+1:03d}_a_question.mp3")
    a1_path  = tmp(f"q{i+1:03d}_b_answer1.mp3")
    a2_path  = tmp(f"q{i+1:03d}_c_answer2.mp3")
    why_path = tmp(f"q{i+1:03d}_d_why.mp3")

    await asyncio.gather(
        speak_to_file(item["q"],                     q_path),
        speak_to_file("The answer is. " + item["a"], a1_path),
        speak_to_file("Again. "          + item["a"], a2_path),
        speak_to_file(item["why"],                   why_path),
    )

    progress.update(1, label=f"Q{i+1}: {item['q'][:38]}...")
    return q_path, a1_path, a2_path, why_path


async def build_episode():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    tmp_dir = os.path.join(OUTPUT_DIR, "_tmp_ep8")
    os.makedirs(tmp_dir, exist_ok=True)

    def tmp(name):
        return os.path.join(tmp_dir, name)

    # Total TTS jobs: intro + outro + 40 questions × 4 clips = 82
    TOTAL_JOBS = 2 + len(QNA) * 4
    # We track at question granularity (40 steps) for the bar
    prog = Progress(total=len(QNA), width=38)

    # ── Step 1: Silence files (instant, no API) ───────────────────────────────
    gap3    = tmp("_silence_3s.mp3")
    gap1    = tmp("_silence_1s.mp3")
    silence_to_file(3, gap3)
    silence_to_file(1, gap1)

    # ── Step 2: Intro and outro (parallel) ───────────────────────────────────
    intro_p = tmp("0000_intro.mp3")
    outro_p = tmp("9999_outro.mp3")
    print("\nGenerating intro and outro...", end="", flush=True)
    await asyncio.gather(
        speak_to_file(INTRO, intro_p),
        speak_to_file(OUTRO, outro_p),
    )
    print(" done.")

    # ── Step 3: Questions in small batches with cool-down ────────────────────
    BATCH_SIZE   = 5        # 5 questions × 4 clips = 20 parallel TTS calls
    COOLDOWN     = 3.0      # seconds between batches to avoid rate-limiting
    all_results  = []

    print(f"\nGenerating {len(QNA)} questions  (batch size {BATCH_SIZE}):")
    prog.set_label("starting...")

    for batch_start in range(0, len(QNA), BATCH_SIZE):
        batch = QNA[batch_start : batch_start + BATCH_SIZE]

        results = await asyncio.gather(*[
            generate_question_block(batch_start + j, item, tmp_dir, prog)
            for j, item in enumerate(batch)
        ])
        all_results.extend(results)

        # Cool-down between batches (skip after last batch)
        if batch_start + BATCH_SIZE < len(QNA):
            prog.set_label(f"cooling down {COOLDOWN:.0f}s...")
            await asyncio.sleep(COOLDOWN)

    prog.done("all questions generated")

    # ── Step 4: Assemble ──────────────────────────────────────────────────────
    print("\nAssembling audio...", end="", flush=True)
    segments = [intro_p, gap1]
    for q_path, a1_path, a2_path, why_path in all_results:
        segments += [q_path, gap3, a1_path, a2_path, why_path, gap1]
    segments.append(outro_p)

    final    = os.path.join(OUTPUT_DIR, OUTPUT_FILE)
    concat_mp3s(segments, final)
    size_mb  = os.path.getsize(final) / (1024 * 1024)
    print(f" done.\n")

    # ── Step 5: Clean up ──────────────────────────────────────────────────────
    for f in os.listdir(tmp_dir):
        os.remove(os.path.join(tmp_dir, f))
    os.rmdir(tmp_dir)

    print(f"  Output : {final}")
    print(f"  Size   : {size_mb:.1f} MB")
    print(f"  Voice  : {VOICE}")
    print(f"  Done ✓")


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    print("\nCS426 Episode 8 — Q&A Podcast Generator")
    print("==========================================")
    asyncio.run(build_episode())


if __name__ == "__main__":
    main()
