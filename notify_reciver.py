import progressbar 

class NotifyReciver:
    
    notify_reciver: object
    live_data: object            


    def __init__(self,_notify_reciver):
        self.notify_reciver = _notify_reciver


    def __call__(self, _string):
        #self.notify_reciver.notify(_string)
        print(_string)


    def setLiveData(self, _string, _value):
        self.live_data = progressbar.ProgressBar(widgets=[_string,
                                                    progressbar.Bar(), 
                                                    progressbar.Percentage(), 
                                                    ' ', 
                                                    progressbar.AdaptiveTransferSpeed(unit='it'),
                                                    ' ',
                                                    progressbar.ETA()],
                                                    max_value=_value) 


    def updateLiveData(self, _value):
        self.live_data.update(_value)

    def finishLiveData(self):
        self.live_data.finish()
