# Local-Dream-Proxy
Connects Local Dream HTTP API requests to sillytavern.

How to install in termux:-

1.install the these requirements

```
pkg update && pkg upgrade
pkg install -y python python-pip
pkg install -y libjpeg-turbo
pkg install -y python-numpy python-pillow
pip install flask pillow requests
```

2. download the script into termux home folder for easy access. you can clone it instead if you want.
```
curl -O https://raw.githubusercontent.com/thewalkingcat/Local-Dream-Proxy/main/LDBridge.py
```

3. run the script. if sillytavern was running on it, make a new instance and run the script on that.
```
python LDBridge.py
```
then it should say : "* Running on http://127.0.0.1:7860" indicating its running successfuly

4. open Local Dream app and choose an image model.

you should see a notification from local dream app that says "Model backend service is running."

6. Configure SillyTavern
Open SillyTavern
Go to Extensions (puzzle piece icon in the top bar)
Select Image Generation from the dropdown
Set Source to: Stable Diffusion WebUI / AUTOMATIC1111
In the API URL field enter: http://127.0.0.1:7860
Click Connect — you should get a confirmation toast

7.configure parameters for your image gen such as schedulers steps cfg and such according to image model. you can refer to local dream's setting because some image models need to be on the right setting for it to actually work.

now you should able to generate the image in sillytavern using local dream's http backend.

How it works:
```
SillyTavern  --->  POST /sdapi/v1/txt2img  --->  LDBridge (:7860)
                                                       |
                                               Translates A1111 to LD format
                                                       |
                                                       v
                                                  Local Dream (:8081)
                                                  POST /generate (SSE)
                                                       |
                                               Raw RGB base64 returned
                                                       |
                                                       v
                                                  LDBridge converts
                                                  Raw RGB -> PNG base64
                                                       |
                                                       v
SillyTavern  <---  A1111 JSON response  <---  LDBridge (:7860)
```
