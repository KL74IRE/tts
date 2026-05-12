"""
CS427 Episode 6 — Q&A Revision Podcast Generator
==================================================
Generates a single MP3 — a spoken Q&A revision session covering all
key concepts from Episodes 1 to 5.

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
    py generate_podcast_cs427_ep6_qna.py

Output:
    audio/CS427_Episode6_QnA_Revision.mp3

Notes:
    - Requires internet connection — edge-tts connects to Microsoft Speech servers
    - Uses Emily (en-IE-EmilyNeural) — Irish female neural voice
    - Run from any folder — the audio subfolder is created automatically
    - SLAM is confirmed NOT on this year's exam and is excluded from all questions
"""

import edge_tts
import asyncio
import os
import re
import struct
import wave

# ── Config ────────────────────────────────────────────────────────────────────
OUTPUT_DIR   = "audio"
OUTPUT_FILE  = "CS427_Episode6_QnA_Revision.mp3"
VOICE        = "en-IE-EmilyNeural"

# ── Content ───────────────────────────────────────────────────────────────────

INTRO = """
Welcome to the CS427 Autonomous Mobile Robotics Q and A Revision Podcast.
This is Episode 6 — your exam preparation session.

This podcast covers all key concepts from Episodes 1 through 5.
It includes wheeled locomotion and kinematics, mobile robot localisation,
sensing and perception, vision and image processing, and ROS 2.

Note: SLAM is confirmed not on this year's exam and has been excluded from all questions.

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

    # ── EPISODE 1: KINEMATICS ──────────────────────────────────────────────────

    {
        "q": "Question 1. What is the rolling constraint for a fixed standard wheel, and what does it physically mean?",
        "a": "The rolling constraint is: sine of alpha plus beta, times x dot, minus cosine of alpha plus beta, times y dot, minus l times cosine of beta, times theta dot, equals r times phi dot. It means the velocity of the wheel contact point along the forward direction must equal r times the wheel's angular velocity — the wheel rolls without slipping.",
        "why": "This is the most important single equation in Module 1. The rolling constraint describes motion along the wheel's forward direction. Every Q1 question requires you to substitute alpha, beta, l, and r into this formula."
    },
    {
        "q": "Question 2. What is the sliding constraint for a fixed standard wheel, and what does it physically mean?",
        "a": "The sliding constraint is: cosine of alpha plus beta, times x dot, plus sine of alpha plus beta, times y dot, plus l times sine of beta, times theta dot, equals zero. It means the velocity perpendicular to the wheel's forward direction must be zero — no lateral slip is allowed.",
        "why": "The sliding constraint equals zero for all fixed standard wheels. This is what you test motion vectors against. If substituting a motion vector gives a non-zero result, the motion is invalid."
    },
    {
        "q": "Question 3. When beta equals zero, what simplification occurs in both the rolling and sliding constraints?",
        "a": "When beta equals zero, cosine of beta equals one and sine of beta equals zero. In the rolling constraint, l times cosine of beta becomes just l. In the sliding constraint, the l times sine of beta term vanishes entirely, removing the theta dot term.",
        "why": "This simplification applies to most Q1 exam questions where wheels are tangential to the platform. Spotting it early saves significant algebra. The sliding constraint becomes simply cosine of alpha times x dot plus sine of alpha times y dot equals zero."
    },
    {
        "q": "Question 4. What is alpha, and how do you read it from a diagram?",
        "a": "Alpha is the angle from the positive X R axis of the robot frame to the position vector of the wheel's ground contact point, measured counter-clockwise. For a wheel at positive X: alpha is zero. At positive Y: alpha is pi over 2. At negative X: alpha is pi. At negative Y: alpha is negative pi over 2.",
        "why": "Alpha is the most commonly misidentified parameter in Q1. You must draw the robot frame, find the wheel's position vector from the origin, and measure the counter-clockwise angle from X R to that vector."
    },
    {
        "q": "Question 5. How do you test whether a motion vector is valid or invalid?",
        "a": "Substitute the motion vector x dot, y dot, theta dot into each wheel's sliding constraint. If every sliding constraint gives zero, the motion is valid. If any sliding constraint gives a non-zero result, the motion is invalid.",
        "why": "Only the sliding constraint is used for validity testing — not the rolling constraint. The rolling constraint is used afterward to find the wheel speed phi dot. This two-step method is essential exam technique."
    },
    {
        "q": "Question 6. For a valid motion, how do you find the angular velocity phi dot of each wheel?",
        "a": "Substitute the valid motion vector x dot, y dot, theta dot into each wheel's rolling constraint and solve for phi dot. Each wheel may give a different phi dot value.",
        "why": "Once a motion passes the sliding constraint test, the rolling constraint gives you the wheel speed directly. If a motion is invalid, you do not proceed to this step."
    },
    {
        "q": "Question 7. What is the degree of mobility delta m, and how is it computed?",
        "a": "The degree of mobility delta m is the number of independent velocity directions the robot can achieve from wheel rolling alone, without changing any steering angle. It is computed as three minus the rank of the sliding constraint matrix C1.",
        "why": "Why three? Because the robot lives in a 2D plane with three degrees of freedom: x, y, and rotation. The rank of C1 tells you how many of those are constrained. The difference gives you the free directions."
    },
    {
        "q": "Question 8. What are degree of steerability and degree of maneuverability, and how are they computed?",
        "a": "Degree of steerability delta s equals the rank of C1 sub s, where C1 sub s is the portion of C1 from steerable wheels only. For platforms with no steerable wheels, delta s is zero. Degree of maneuverability delta M equals delta m plus delta s.",
        "why": "Delta M is the total number of independent motions available to the platform. A differential drive robot has delta M of 2 — it can drive and spin. A platform that can only spin in place has delta M of 1."
    },
    {
        "q": "Question 9. How do you build the matrix C1 from the wheel constraints, and what is the most common mistake when computing its rank?",
        "a": "C1 is formed by stacking the sliding constraint row from every wheel into a single matrix. Each row contains the coefficients of x dot, y dot, and theta dot from that wheel's sliding constraint. The most common mistake is counting all rows as independent — you must check for duplicate rows first.",
        "why": "On symmetric platforms, opposite wheels often give identical sliding constraints. For example, on a four-wheel circular platform, wheels 1 and 3 both give x dot equals zero, so their rows are identical and only count once. The rank is 2, not 4."
    },
    {
        "q": "Question 10. For a Swedish wheel with roller angle gamma, how does the sliding constraint differ from a fixed wheel?",
        "a": "For a Swedish wheel, the sliding constraint does not equal zero. Instead it equals r times phi dot times sine of gamma, plus r sub sw times phi dot sub sw. This means the inner rollers can spin to allow motion in the previously forbidden lateral direction, making the wheel omnidirectional.",
        "why": "This is the key difference between fixed and Swedish wheels. A fixed wheel imposes a hard lateral velocity constraint of zero. A Swedish wheel relaxes this constraint by allowing the inner rollers to contribute. For a 90-degree Swedish wheel, sine of gamma equals one."
    },

    # ── EPISODE 2: LOCALISATION ────────────────────────────────────────────────

    {
        "q": "Question 11. What is the belief distribution bel of x t, and what does it represent?",
        "a": "The belief bel of x t is a probability distribution over all possible robot poses at time t, given all controls and measurements up to time t. It represents the robot's uncertainty about its own location — rather than a single estimate, it tracks a full distribution over where the robot might be.",
        "why": "This probabilistic approach is what makes Markov localisation robust to sensor noise. Instead of committing to one pose estimate, the belief captures all possibilities weighted by their probability."
    },
    {
        "q": "Question 12. What is the Markov assumption, and why is it important for localisation?",
        "a": "The Markov assumption states that the current state x t depends only on the previous state x t minus 1 and the current control u t. It does not depend on anything older than one time step. This allows the full history of controls and measurements to be summarised as just the previous belief, making the algorithm computationally tractable.",
        "why": "Without the Markov assumption, the algorithm would need to track the entire history of robot poses and sensor readings, which grows unboundedly over time. The Markov assumption makes localisation solvable in real time."
    },
    {
        "q": "Question 13. Explain the prediction step of the Markov localisation algorithm.",
        "a": "The prediction step computes bel bar of x t as the integral over all previous poses of p of x t given x t minus 1 and u t, times bel of x t minus 1, with respect to x t minus 1. It marginalises out the previous pose by summing — or integrating — over all possible previous locations, weighted by the motion model and the old belief. The result is more uncertain than the previous belief because motion is noisy.",
        "why": "The prediction step is a convolution of the previous belief with the motion model. It propagates uncertainty forward in time. In the discrete version, the integral becomes a sum over all grid cells."
    },
    {
        "q": "Question 14. Explain the update step of the Markov localisation algorithm.",
        "a": "The update step computes bel of x t as eta times p of z t given x t and M, times bel bar of x t. It multiplies the predicted belief by the sensor likelihood — how likely is the sensor reading z t if the robot were at pose x t in map M. Poses that match the sensor reading well get higher probability. Eta normalises the result so all probabilities sum to one.",
        "why": "The update step is a Bayes update. It sharpens the belief distribution around poses consistent with the sensor reading. After the update, the belief is more certain than the predicted belief."
    },
    {
        "q": "Question 15. How do you compute the discrete prediction step numerically?",
        "a": "For each possible new pose x t, sum over all possible previous poses x t minus 1 the product of the motion model probability p of x t given x t minus 1 and u t, times the old belief bel of x t minus 1. This is a weighted sum — each old cell contributes to nearby new cells according to the motion model.",
        "why": "This numerical computation appears in Summer 2025 Q4 b and Autumn 2025 Q4 b. You are given a table of old belief values and a motion model table giving transition probabilities for displacements of zero, one, two, and so on. Multiply and sum carefully for each new position."
    },
    {
        "q": "Question 16. How does the three-pixel sensor likelihood model work?",
        "a": "The three-pixel sensor looks behind the robot, at the robot's current position, and in front of the robot. Each pixel independently detects either a landmark or free space. For each pixel, you look at the map at that position. If the map shows a landmark and the sensor detected it, use P of Detection given Present. If the map shows free space and the sensor did not detect, use P of not-detected given not-present. Multiply all three pixel probabilities together.",
        "why": "Because the pixels are independent, the joint likelihood is the product of the individual likelihoods. This numerical calculation appears in Autumn 2024 Q4 b and Summer 2025 Q4 c with different sensor probabilities each time."
    },
    {
        "q": "Question 17. What are the false positive and false negative rates for a sensor with P of Detection given Present equal to 0.85?",
        "a": "The false negative rate — missing a landmark that is there — is one minus 0.85, which equals 0.15. If P of not-detected given not-present is 0.95, the false positive rate — detecting a landmark that is not there — is one minus 0.95, which equals 0.05.",
        "why": "You need these complementary probabilities when a pixel reads a landmark but the map shows free space, or vice versa. Always derive them from the given detection probabilities rather than guessing."
    },
    {
        "q": "Question 18. How does a particle filter represent the belief distribution?",
        "a": "A particle filter represents the belief as a set of M weighted samples called particles. Each particle is a hypothesis about where the robot might be. The density of particles in a region approximates the probability of the robot being in that region. Higher weight particles are more consistent with the sensor readings.",
        "why": "Unlike grid-based Markov localisation which requires memory proportional to map size, particle filters concentrate computation where the robot is likely to be. As more measurements come in, particles cluster around the true pose."
    },
    {
        "q": "Question 19. What are the three steps of the particle filter algorithm?",
        "a": "Step one: sample. For each particle from the previous time step, draw a new particle from the motion model — add noise to represent uncertainty in motion. Step two: weight. Compute an importance weight for each new particle equal to eta times p of z t given x t and M. Step three: resample. Draw M new particles from the weighted set, with probability proportional to weight.",
        "why": "After resampling, high-weight particles are copied multiple times and low-weight particles are dropped. This concentrates the particle set around likely poses. Over time the particle cloud converges to the true location."
    },
    {
        "q": "Question 20. What is the difference between roulette wheel resampling and low variance resampling?",
        "a": "Roulette wheel resampling spins a weighted wheel M times independently, with order of M log M complexity. Low variance resampling draws a single random starting point r from Uniform zero to one over M, then samples at regular intervals of one over M. It has order M complexity and maintains better particle diversity.",
        "why": "Low variance resampling is preferred because it avoids duplicate particles dominating the set. With roulette wheel resampling, unlucky draws can produce many copies of the same particle and miss good ones. Low variance guarantees uniform coverage of the weight distribution."
    },

    # ── EPISODE 3: SENSING ────────────────────────────────────────────────────

    {
        "q": "Question 21. What is the difference between proprioceptive and exteroceptive sensors?",
        "a": "Proprioceptive sensors measure the robot's internal state — such as wheel encoders measuring rotation or gyroscopes measuring angular velocity. Exteroceptive sensors measure the external environment — such as laser scanners measuring distance to obstacles or cameras capturing images of the surroundings.",
        "why": "This classification appears in Q2 sensor questions. Examples of proprioceptive sensors: encoders, IMU. Examples of exteroceptive sensors: lidar, camera, sonar. Active sensors emit energy and measure the response. Passive sensors only measure ambient energy."
    },
    {
        "q": "Question 22. How does a MEMS gyroscope measure angular velocity?",
        "a": "A MEMS gyroscope uses a tiny vibrating proof mass suspended by springs inside a silicon chip. When the chip rotates, the Coriolis effect deflects the vibrating mass perpendicular to its vibration direction. This deflection is measured by changes in capacitance between comb-like electrodes. The deflection magnitude is proportional to the angular velocity.",
        "why": "MEMS gyroscopes appear in Q2 sensor questions in Autumn 2024 and Summer 2025. Key facts: Coriolis effect, vibrating proof mass, capacitive measurement, proportional to angular velocity. A diagram showing the proof mass and electrodes is expected in the exam."
    },
    {
        "q": "Question 23. How does a fibre optic gyroscope measure angular velocity?",
        "a": "Two laser beams travel around a coiled optical fibre loop in opposite directions. When the sensor rotates, the Sagnac effect causes the two beams to travel slightly different path lengths. This produces a measurable phase difference between the beams proportional to the angular velocity.",
        "why": "The key principle is the Sagnac effect. Fibre optic gyros are more accurate than MEMS gyros but more expensive. They are used in high-precision navigation systems. The counter-rotating beams and phase difference are the key details."
    },
    {
        "q": "Question 24. How does a 2D LiDAR work, and what does it produce?",
        "a": "A 2D LiDAR emits short laser pulses from a rotating mirror. It measures the round-trip time for each pulse to return after reflecting off an object. Distance equals speed of light times time divided by two. As the mirror rotates, it measures distance at each bearing angle, producing a 2D slice of range measurements covering 360 degrees.",
        "why": "LiDAR appears in Q2 sensor questions in Autumn 2024 and Summer 2025. Key facts: pulsed laser, rotating mirror, time of flight principle, produces 2D point cloud. A 3D LiDAR uses multiple laser beams at different vertical angles to produce a full 3D point cloud."
    },
    {
        "q": "Question 25. How does the Kinect version 1 structured light sensor work, and what is its geometric analogy?",
        "a": "The Kinect version 1 projects a fixed pattern of infrared dots onto the scene. A separate infrared camera images the dots. The apparent displacement of each dot from its expected position is proportional to depth — geometrically analogous to a fronto-parallel stereo sensor where the projector plays the role of one camera and the IR camera plays the other.",
        "why": "This geometric analogy to fronto-parallel stereo appears directly in Summer 2025 Q2 d. The key insight is that the projector and camera are separated by a known baseline, and disparity between the projected and observed dot positions gives depth via Z equals f times b divided by disparity."
    },
    {
        "q": "Question 26. How does the Kinect version 2 time of flight sensor calculate depth?",
        "a": "The Kinect version 2 emits modulated near-infrared light. Each pixel captures the returning light in two charge integration windows Q1 and Q2 at different times. Depth is calculated as d equals one half times c times delta t times Q2 divided by Q1 plus Q2, where c is the speed of light and delta t is the modulation period.",
        "why": "This formula appears directly in Autumn 2024 Q2 b. Q2 over Q1 plus Q2 is a ratio that encodes the phase shift of the returning light. When the object is closer, more light returns during Q2, shifting the ratio. You should be able to define every term in this formula."
    },
    {
        "q": "Question 27. What is the GPS trilateration process, and what are the accuracies of GPS, DGPS, and RTK?",
        "a": "GPS satellites broadcast pseudorandom noise signals with timestamps. The receiver measures the time delay to compute distance as speed of light times delay. With four satellites you solve for x, y, z position and clock error. Standard GPS accuracy is 5 to 10 metres. DGPS uses a ground reference station to broadcast error corrections, improving accuracy to about 40 centimetres. RTK uses carrier phase measurements to achieve 1 to 2 centimetre accuracy.",
        "why": "GPS appears in Summer 2024 Q2 a. The key numbers are: GPS 5 to 10 metres, DGPS 40 centimetres, RTK 1 to 2 centimetres. Note it is trilateration — using distances — not triangulation — which uses angles. This distinction costs marks."
    },
    {
        "q": "Question 28. What is a GPS-aided INS, and why does combining the two sensors work better than either alone?",
        "a": "An INS or Inertial Navigation System uses gyroscopes and accelerometers to estimate orientation and position by integration. It provides high-frequency motion updates but accumulates drift over time. GPS provides absolute position at low frequency but is accurate over the long term. GPS-aided INS combines both — GPS corrects IMU drift and IMU bridges GPS outages. Their error characteristics are complementary.",
        "why": "The key phrase is complementary error characteristics. GPS errors are long-term stable but short-term noisy. IMU errors are short-term stable but long-term drifting. Together they cover each other's weaknesses."
    },

    # ── EPISODE 4: VISION ─────────────────────────────────────────────────────

    {
        "q": "Question 29. What is the full camera projection equation, and what does each matrix represent?",
        "a": "The equation is p equals K times Pi zero times T w c times P w. K is the 3 by 3 intrinsic matrix containing focal lengths f x and f y in pixels and the principal point u zero and v zero. Pi zero is the 3 by 4 standard projection matrix that drops the homogeneous coordinate. T w c is the 4 by 4 extrinsic matrix transforming from world coordinates to camera coordinates.",
        "why": "This equation appears in Autumn 2025 Q2 b and c. K encodes the camera's internal properties. T w c encodes where the camera is in the world. Pi zero performs the actual projection from 3D to 2D. Knowing the dimensions of each matrix is required."
    },
    {
        "q": "Question 30. Why is a monocular camera called a bearing-only sensor?",
        "a": "A monocular camera can only measure the direction — or bearing — to a point in 3D space from a single image. The depth Z appears in the denominator of the projection equations x equals f times X over Z and y equals f times Y over Z, so different 3D points at different depths can project to the same image pixel. Depth is unobservable from a single view.",
        "why": "This is a fundamental limitation of monocular cameras. Stereo cameras recover depth by comparing the projections from two different viewpoints. The disparity between the two projections encodes depth."
    },
    {
        "q": "Question 31. Derive the depth from disparity formula for a fronto-parallel stereo system.",
        "a": "The left camera projects point P with coordinates X, Y, Z to u l equals f times X over Z. The right camera is offset by baseline b, so it projects to u r equals f times X minus b over Z. The disparity is d equals u l minus u r equals f times b over Z. Rearranging gives depth Z equals f times b divided by u l minus u r.",
        "why": "This formula appears as a numerical calculation in Summer 2024 Q2 d and Summer 2025 Q2 c. Given f, b, and a 3D point P, compute u l and u r separately, subtract to get disparity, then verify with Z equals f times b over disparity."
    },
    {
        "q": "Question 32. What is the essential matrix E, and what is the epipolar constraint?",
        "a": "The essential matrix E equals t cross times R, where t is the translation between the two cameras and R is the rotation. The epipolar constraint states that for any correctly matched pair of normalised image points p l prime and p r prime: p r prime transpose times E times p l prime equals zero.",
        "why": "The essential matrix encodes the geometric relationship between two calibrated cameras. The epipolar constraint reduces the correspondence search from 2D to 1D — the matching point must lie on the epipolar line defined by E times p l prime. This appears in Autumn 2024 Q2 c and Autumn 2025 Q2 d."
    },
    {
        "q": "Question 33. How does the 8-point algorithm estimate the essential matrix?",
        "a": "For each matched pair of points, write the epipolar constraint p r prime transpose E p l prime equals zero as a linear equation in the 9 unknown entries of E. With 8 or more pairs, this forms an overdetermined system D times e equals zero. Solve using singular value decomposition — the solution is the right singular vector corresponding to the smallest singular value. Then enforce the rank-2 constraint on E by zeroing its smallest singular value.",
        "why": "The 8-point algorithm appears in Autumn 2024 Q2 c and Autumn 2025 Q2 d. The key steps are: form the linear system, solve with SVD, enforce rank 2. You do not need to perform the SVD by hand in the exam — just explain the procedure."
    },
    {
        "q": "Question 34. How does the Harris corner detection algorithm work?",
        "a": "Step one: compute image gradients I x and I y using Sobel filters. Step two: compute products I x squared, I x times I y, and I y squared. Step three: sum these products over a local window to build the 2 by 2 autocorrelation matrix M. Step four: compute the Harris response C equals determinant of M minus kappa times trace of M squared. Step five: threshold C and apply non-maximum suppression.",
        "why": "Harris appears in Q3 in three of four past papers. The autocorrelation matrix M is 2 by 2 — it has at most 2 eigenvalues, not 3. Both eigenvalues large means corner. One large means edge. Both small means flat region."
    },
    {
        "q": "Question 35. What do SAD, SSD, and NCC measure, and what is the key direction difference between them?",
        "a": "SAD is Sum of Absolute Differences — sum the absolute pixel differences. Lower SAD means more similar. SSD is Sum of Squared Differences — sum the squared pixel differences. Lower SSD means more similar. NCC is Normalised Cross Correlation — computes correlation after subtracting means and normalising. Higher NCC means more similar. NCC is bounded between minus one and plus one and is invariant to brightness and contrast changes.",
        "why": "The direction difference is critical: SAD and SSD — lower is better. NCC — higher is better. NCC is the most discriminative because it handles brightness differences. SAD and SSD are sensitive to intensity scale."
    },
    {
        "q": "Question 36. What are the four steps of SIFT, and what size is the final descriptor?",
        "a": "Step one: build a Difference of Gaussians pyramid and detect local extrema as keypoint candidates. Step two: assign orientation from dominant gradient direction in local neighbourhood — makes SIFT rotation invariant. Step three: take a 16 by 16 region, divide into a 4 by 4 grid, compute an 8-bin orientation histogram per sub-region, concatenate to get a 128-dimensional descriptor — 4 times 4 times 8. Step four: match using Euclidean distance with ratio test — accept if d1 over d2 is less than 0.7.",
        "why": "SIFT appears in Summer 2024 Q3 b. The 128-dimensional descriptor and the ratio test threshold of 0.7 are specific numbers you must know. SIFT is scale-invariant because of the pyramid — Harris is not."
    },
    {
        "q": "Question 37. What is the Bag-of-Words approach to visual place recognition?",
        "a": "Step one: build a visual vocabulary by extracting SIFT descriptors from many images and clustering with k-means — each cluster centre is a visual word. Step two: represent each image as a histogram of visual word counts — the BoW vector. Step three: apply tf-idf weighting where t i equals n id over n d times log of N over n i — this down-weights common words. Step four: use an inverted file index for efficient retrieval — each word stores a list of images containing it.",
        "why": "BoW appears in Summer 2024 Q3 c, Autumn 2024 Q3 c and d, and Summer 2025 Q3 c. The tf-idf formula is a numerical exam question. n i is the number of documents containing word i — not the total count of word i across all documents. This distinction is commonly confused."
    },

    # ── EPISODE 5: ROS 2 ──────────────────────────────────────────────────────

    {
        "q": "Question 38. What is the purpose of the colcon utility in ROS 2, and what did it replace?",
        "a": "Colcon is the build tool for ROS 2 packages. You run colcon build in your workspace to compile all packages. It replaced catkin from ROS 1.",
        "why": "This appears in Autumn 2025 Q2 a. ROS 2 introduced colcon as a more flexible and language-agnostic build tool compared to catkin. All six ROS 2 changes from Autumn 2025 are examinable: colcon, ros2 CLI, no master node, rcl, language constraints, and Python launch files."
    },
    {
        "q": "Question 39. What are three key changes from ROS 1 to ROS 2?",
        "a": "First: the ROS master node has been removed and replaced by DDS — Data Distribution Service — a peer-to-peer middleware where nodes discover each other directly. Second: all command-line tools like rostopic and roslaunch are unified under a single ros2 command. Third: launch files can now be written in Python rather than XML only, allowing full Python logic in the launch process.",
        "why": "These three changes appear in Autumn 2025 Q2 a. The removal of the master node is the most architecturally significant change — it makes the system more robust by eliminating a single point of failure. RCL — the ROS Client Library — is also new: it is a C abstraction layer that rclcpp and rclpy sit on top of."
    },
    {
        "q": "Question 40. In the ROS computation graph for a differential drive robot, what is the role of inv diff drive kinematics and diff drive kinematics?",
        "a": "The inv diff drive kinematics node takes the desired platform velocity command from the slash cmd vel topic and computes the individual wheel velocities required to achieve it, publishing them to slash wheel vels. The diff drive kinematics node takes the wheel velocities and computes the forward kinematics — estimating how the platform has actually moved — publishing joint states to slash joint states and updating the transform tree via slash tf.",
        "why": "This ROS computation graph appears in Summer 2025 Q1 b. There are two kinematics nodes: inverse kinematics converts desired motion to wheel speeds, forward kinematics converts wheel speeds back to estimated motion for odometry. Understanding the direction of information flow is key."
    },
]

OUTRO = """
That is the end of your CS427 Q and A revision session.

You have covered 40 questions across all five topics —
wheeled locomotion and kinematics,
mobile robot localisation,
sensing and perception,
vision and image processing,
and ROS 2.

Remember: SLAM is confirmed not on this year's exam.

Key formulas to have memorised before your exam:

Rolling constraint: sine of alpha plus beta times x dot, minus cosine of alpha plus beta times y dot, minus l cosine beta times theta dot, equals r phi dot.

Sliding constraint: cosine of alpha plus beta times x dot, plus sine of alpha plus beta times y dot, plus l sine beta times theta dot, equals zero.

Depth from disparity: Z equals f times b divided by u l minus u r.

Degree of mobility: delta m equals 3 minus rank of C1.

Degree of maneuverability: delta M equals delta m plus delta s.

Prediction step: bel bar of x t equals the sum over x t minus 1 of p of x t given x t minus 1 and u t, times bel of x t minus 1.

Update step: bel of x t equals eta times p of z t given x t and M, times bel bar of x t.

tf-idf: t i equals n i d over n d times log of N over n i.

Harris response: C equals determinant of M minus kappa times trace of M squared.

Good luck in your exam. You have done the work. Now go prove it.
"""

# ── TTS helpers ───────────────────────────────────────────────────────────────

def clean(text):
    text = re.sub(r'  +', ' ', text)
    return text.strip()


async def speak_to_file(text, path):
    communicate = edge_tts.Communicate(text=clean(text), voice=VOICE)
    await communicate.save(path)


def silence_to_file(seconds, path):
    """Generate a true silent audio file using pure Python — no API call needed."""
    sample_rate = 44100
    num_samples = int(sample_rate * seconds)
    wav_path = path.replace('.mp3', '.wav')
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


async def generate_question_block(i, item, tmp_dir):
    """Generate all 4 audio segments for one question simultaneously."""
    def tmp(name):
        return os.path.join(tmp_dir, name)

    q_path   = tmp(f"q{i+1:03d}_a_question.mp3")
    a1_path  = tmp(f"q{i+1:03d}_b_answer1.mp3")
    a2_path  = tmp(f"q{i+1:03d}_c_answer2.mp3")
    why_path = tmp(f"q{i+1:03d}_d_why.mp3")

    # Fire all 4 TTS calls at the same time
    await asyncio.gather(
        speak_to_file(item["q"], q_path),
        speak_to_file("The answer is. " + item["a"], a1_path),
        speak_to_file("Again. " + item["a"], a2_path),
        speak_to_file(item["why"], why_path),
    )
    return q_path, a1_path, a2_path, why_path


async def build_episode():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    tmp_dir = os.path.join(OUTPUT_DIR, "_tmp_ep6")
    os.makedirs(tmp_dir, exist_ok=True)

    def tmp(name):
        return os.path.join(tmp_dir, name)

    # ── Step 1: Silence, intro and outro ─────────────────────────────────────
    print("Step 1/3 — Generating silence, intro and outro in parallel...")
    gap3    = tmp("_silence_3s.mp3")
    gap1    = tmp("_silence_1s.mp3")
    intro_p = tmp("0000_intro.mp3")
    outro_p = tmp("9999_outro.mp3")

    silence_to_file(3, gap3)
    silence_to_file(1, gap1)
    await asyncio.gather(
        speak_to_file(INTRO, intro_p),
        speak_to_file(OUTRO, outro_p),
    )
    print("  Done.\n")

    # ── Step 2: All 40 questions in parallel batches of 10 ───────────────────
    BATCH_SIZE = 10
    all_results = []

    print(f"Step 2/3 — Generating {len(QNA)} questions in batches of {BATCH_SIZE}...")
    for batch_start in range(0, len(QNA), BATCH_SIZE):
        batch     = QNA[batch_start:batch_start + BATCH_SIZE]
        batch_end = min(batch_start + BATCH_SIZE, len(QNA))
        print(f"  Questions {batch_start+1} to {batch_end}...")

        results = await asyncio.gather(*[
            generate_question_block(batch_start + j, item, tmp_dir)
            for j, item in enumerate(batch)
        ])
        all_results.extend(results)

    print("  Done.\n")

    # ── Step 3: Assemble in order and concatenate ─────────────────────────────
    print("Step 3/3 — Assembling and concatenating...")
    segments = [intro_p, gap1]

    for q_path, a1_path, a2_path, why_path in all_results:
        segments.append(q_path)    # Question
        segments.append(gap3)      # 3 second thinking gap
        segments.append(a1_path)   # Answer first time
        segments.append(a2_path)   # Answer second time
        segments.append(why_path)  # Explanation
        segments.append(gap1)      # 1 second gap

    segments.append(outro_p)

    final = os.path.join(OUTPUT_DIR, OUTPUT_FILE)
    concat_mp3s(segments, final)

    size_mb = os.path.getsize(final) / (1024 * 1024)
    print(f"\nDone. Saved: {final}  ({size_mb:.1f} MB)")

    # Clean up temp files
    for f in os.listdir(tmp_dir):
        os.remove(os.path.join(tmp_dir, f))
    os.rmdir(tmp_dir)
    print("Temp files cleaned up.")


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    print("\nCS427 Episode 6 — Q&A Podcast Generator")
    print("==========================================")
    print(f"Voice:      {VOICE}")
    print(f"Questions:  {len(QNA)}")
    print(f"Output:     {OUTPUT_DIR}/{OUTPUT_FILE}\n")
    asyncio.run(build_episode())


if __name__ == "__main__":
    main()