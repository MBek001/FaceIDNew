# Terminal Documentation

## What the Terminal Page Does

The terminal lives at `/terminal/`. It is a full-screen dark page with two buttons:
- **✅ KELDI** (left, dark green) — marks arrival
- **🚪 KETDI** (right, dark red) — marks departure

A live clock in Asia/Tashkent timezone is displayed at the top.

No authentication is required. The terminal is designed to run on a dedicated device in the office.

---

## Webcam Capture Sequence

1. User presses KELDI or KETDI.
2. Browser requests webcam access via `navigator.mediaDevices.getUserMedia`.
3. Video stream is displayed in a centered overlay.
4. Countdown shows: **3... 2... 1...** (each digit held for exactly 1 second).
5. At 0, the current video frame is drawn to a hidden `<canvas>`.
6. All webcam tracks are stopped immediately after capture.
7. The canvas is converted to a JPEG blob via `canvas.toBlob()`.
8. A POST request is sent to `/terminal/scan/` with the image and action.
9. A spinner is shown while waiting for the server response.

---

## Face Matching Algorithm (Server Side)

1. `decode_image_to_rgb_array()` — Opens the JPEG with Pillow, converts to RGB numpy array.
2. `face_recognition.face_locations(rgb_array)` — Detects face bounding boxes.
3. If 0 faces: return error "No face detected".
4. If 2+ faces: return error "Multiple faces".
5. `face_recognition.face_encodings(rgb_array, locations)` — Compute 128-float encoding.
6. For each registered user, compute `face_recognition.face_distance([stored], incoming)`.
7. Pick the user with the smallest distance that is below `FACE_TOLERANCE` (default 0.5).
8. Lower distance = more confident match. 0.0 = identical, 1.0 = no similarity.
9. Return matched user and distance, or None if no match within tolerance.

---

## Error Types and Their Causes

| HTTP Status | Error Message | Cause |
|---|---|---|
| 400 | Invalid action | `action` field not "came" or "gone" |
| 400 | No image | `image` file not in POST |
| 422 | No face detected | face_recognition found 0 faces |
| 422 | Multiple faces | face_recognition found 2+ faces |
| 401 | Face not recognized | No registered user matches within FACE_TOLERANCE |
| 200 | success: true | Scan recorded, Celery task dispatched |

Client-side errors (webcam denied, network failure) are shown with 4-second dismissal.
Server errors are also shown and dismissed after 4 seconds.
Success results are shown for 5 seconds, then the UI resets to the two-button state.

---

## Why Raw Events Are Never Modified

`AttendanceEvent` has `has_add_permission`, `has_change_permission`, and `has_delete_permission` all returning `False` in the admin. The model itself has no update methods. The `ScanView` only calls `objects.create()`.

This design guarantees that if a bug is found in session computation, or a shift assignment is changed, the original scan record is intact. The `WorkSession` layer can be wiped and recomputed from scratch using the management command, recovering the correct attendance data.
