# proactivity / Pro Voice

## Howto start

Dependency: [uv package manager](https://docs.astral.sh/uv/getting-started/installation/) and [carla](https://carla.readthedocs.io/en/latest/start_quickstart/)

```
# With running `CarlaUE4.exe -quality-level=Low`, execute following in project root directory
uv sync
uv run drive
# in another terminal tab
uv run provoice participantid=001 environment=city secondary_task=none functionname="Adjust seat positioning" modeltype=combined state_model=xlstm w_fcd=0.7 
```

This way it is using my GPU, but its just optional.

## Or you use the Dockerfile

```
# With running CarlaUE4.exe, execute following in project root directory
uv sync
uv run python src/ProVoice/drive.py # is still needed because it relies on Windows API
docker compose up 
```


### For linux

On linux you can start Carla by using the docker image. But it is not working well with wayland.

`src/ProVoice/drive.py` exits with:

`[ERROR] Windows only.`

Only `src/ProVoice/main.py` works out of the box on linux with this setup right now. 

## first-working-title(Julian)

Explainable Proactivity in In-Vehicle Assistants: Effects of Justifications on 
Trust, Transparency, and Workload

## abstract(Julian)

Proroactive in-vehicle assistants take system-initiated actions on behalf of drivers, such as
rejecting calls or changing routes, yet drivers often do not understand why these interventions
occur. A lack of transparency risks undermining appropriate trust and may increase perceived
workload in safety-critical contexts. This work investigates how different explanation strategies
for proactive interventions shape drivers’ experience of such assistants. We will integrate an
explanation module into the existing ProVoice system and run a within-subjects driving-
simulator study, comparing three conditions: no explanation, brief natural-language
explanations, and more detailed, structured explanations presented via the in-vehicle interface.
We will measure trust in automation, perceived transparency and understanding, mental
workload, and acceptance. We expect that explanations will increase trust and transparency
compared to no explanation, while highly detailed explanations may introduce additional
cognitive load. Our findings will inform designers and automotive stakeholders about how to
communicate proactive actions in a way that supports appropriate trust and safety without
overloading drivers.

## abstract(Jiaxuan Li)

With the development of autonomous driving technology, how to reasonably allocate the initiative between human drivers and intelligent systems during driving has become a key issue. Existing studies have proposed five levels of automation and twelve functional feature dimensions, and have used machine learning methods to predict the appropriate system initiative level in different scenarios. However, current research relies on high-level environmental variables rather than real-time traffic inputs. Driver state extraction is primarily based on facial or hand movements, which are susceptible to lighting conditions, while important behavioral signals such as steering and pedal operations are often neglected. In addition, the predictive results still face limitations in interpretability, cross-driver generalization, and personalized adaptation.
To address these limitations, we plan to introduce real-time object detection algorithms to capture dynamic road information and improve system robustness in low-light scenarios, while integrating additional driving behavior features. We will also evaluate the model’s generalization performance across different drivers and design mechanisms that allow for user-specific personalization. This study is expected to enhance the accuracy and interpretability of system initiative prediction, making it more intuitive for drivers, and to increase trust in intelligent systems without reducing driver control, thereby reducing driving workload and potential risks.

one more point: better algorithms to predict?


