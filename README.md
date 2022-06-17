# friendly_idle

This provides a "live patched" [1] version of IDLE to include friendly/friendly-traceback.

Install using the usual `pip install friendly_idle`.

Requires either Python 3.8.10, or Python >= 3.9.5.

You can launch it from a terminal using `friendly_idle`.

![image](https://user-images.githubusercontent.com/629698/174356637-2bf86ecd-a817-4189-89eb-3939c4122dd9.png)

That's it. From there on, if your code triggers a traceback, you will be able to get
interactive help from the embedded version of friendly/friendly-traceback.

![image](https://user-images.githubusercontent.com/629698/174356738-58d3af3f-a8ac-469a-b98e-16648961916b.png)


Please see https://friendly-traceback.github.io/docs/index.html for information about friendly/friendly-traceback.

---

[1] By "live patched", I mean that it uses regular IDLE but patches a few modules as they are imported.
