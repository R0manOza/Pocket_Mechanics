# Data Flow Template

**Feature being traced:**
**“Identify a car part from an uploaded engine-bay photo and answer a follow-up maintenance question.”**



## Step 1 — User Action

The user uploads a photo of their car’s engine bay on the main diagnostic screen, types a question such as **“What part is this and where do I put oil?”** in the text input, and clicks the **“Analyze”** button.



## Step 2 — Preprocessing

The uploaded image is checked for file type and size. If the file is too large or not an image, the user sees an error message and the request is not sent. If valid, the image is resized to a maximum dimension of 1280px while preserving aspect ratio and compressed to JPEG to reduce payload size. The image is then base64-encoded or attached as an image input, depending on the API format.

The user’s text question is trimmed of leading and trailing whitespace, checked for minimum length, and limited to a maximum number of characters to prevent overly large requests.

If the user has previously saved car profile data, such as make, model, year, and known past issues, that structured data is retrieved from the app database before the API call.


## Step 3 — Prompt Construction

**System prompt:**
The system prompt contains instructions telling the model that it is a beginner-friendly car maintenance assistant. It instructs the model to analyze the uploaded engine-bay image, identify visible parts as carefully as possible, use the saved car profile as context when available, avoid pretending to be certain when the image is unclear, and explain results in simple language. It also tells the model to provide safety-conscious guidance and to clearly separate identified parts, uncertainty notes, and next-step advice.

Example system prompt content:

> “You are a car maintenance assistant for non-mechanic users. Analyze the uploaded engine-bay image and answer the user’s question using the car profile when available. Identify likely visible parts, explain their function in simple language, and give safe next-step guidance. If the image is unclear or the part cannot be identified confidently, say so clearly and ask for a better angle or closer photo. Do not invent hidden parts that are not visible.”

**User message content:**
The user message contains:

* the uploaded engine-bay image
* the user’s typed question
* the saved car profile, if available, such as make, model, year, engine
* optionally, a short summary of previous reported issues relevant to that car

Example inserted content:

* Car profile: “2014 Ford Focus, 2.0L engine”
* Previous issue history: “User previously reported coolant bubbling and asked about oil change location”
* User question: “What part is this and where do I put oil?”
* Image: uploaded engine-bay photo

## Step 4 — API Call

**Model:** `Gemini 3 Flash` or another multimodal vision-capable model chosen for the prototype
**Route:** OpenRouter or depending on final implementation
**Key parameters:** low temperature for more stable answers, moderate max token limit, timeout for failed requests

Example version:

* **Model:** a vision-capable model via OpenRouter
* **Route:** `https://openrouter.ai/api/v1`
* **Parameters:** `temperature=0.2`, `max_tokens=800`


## Step 5 — Response Parsing

The API returns a text response containing the identified part, explanation, and guidance. In the safer version of the system, the model is instructed to return a structured JSON object or a clearly labeled text format.

For example, the app may expect fields such as:

* `identified_part`
* `confidence_note`
* `explanation`
* `next_steps`
* `safety_warning`

If JSON is used, the app parses the returned text into a JSON object. If parsing fails, the result is treated as malformed and the system switches to the fallback path.

If plain text is used instead, the app extracts the full answer as a single displayable response and skips structured parsing.

Malformed responses are handled by showing a user-friendly retry message rather than a technical parsing error.



## Step 6 — Confidence or Validation

The app does not rely on a true model confidence score unless the chosen API provides one. Instead, it uses validation rules.

We check:

* whether the response is non-empty
* whether the identified part field exists, if structured output is used
* whether the model explicitly says the image is unclear
* whether the response contains strong uncertainty language such as “cannot identify,” “unclear image,” or “not enough visible detail”

**Threshold / rule:**

* If the response includes a plausible identified part and usable explanation, show it directly.
* If the response says the image is unclear or no part can be identified safely, do not present the result as certain.
* If parsing fails or the response is empty, trigger the failure fallback.

**If below threshold:**
The app asks the user to upload a clearer photo, a closer view, or another angle, and avoids giving specific mechanical instructions based on an uncertain identification.



## Step 7 — User Output

**Success path:**
The user sees a result card on the analysis screen showing:

* the likely part name
* a plain-language explanation of what the part does
* a short answer to the user’s question
* suggested next steps
* any safety note if relevant

The uploaded image remains visible as a thumbnail so the user knows which photo was analyzed. If car profile memory was used, the answer may also mention that the result was tailored to the saved car model.

Example success display:
**Likely part:** Oil filler cap
**What it does:** This is where engine oil is added.
**Next step:** Make sure the engine is off and cool before opening it. Use the oil type recommended for your car.

**Fallback path:**
If the image is unclear or the response is invalid, the user sees a message such as:

> “We could not identify the part confidently from this photo. Please upload a clearer image from a closer distance or a different angle.”

The screen shows a **“Try Again”** button and keeps the user’s question in the text field so they do not need to retype it.
