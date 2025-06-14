Listing 1 – Detection Process 

def run(self) -> None:     self.__init()     self._health_checker.beat(         type=HealthDataType.DATA,         data='START'     )     try:         while self._continue_work():             if self.__image_queue.empty():                 time.sleep(self.__sleep_time_attempting_get_task)                 continue              cap_image: CapturedImage = self.__image_queue.get()             image = cap_image.get_image()             predictions = self.__net.image_detection(image)             result = DetectionResult(                 cap_image=cap_image,                 predictions=predictions             )             self.__result_queue.put(result)      except Exception as ex:         self._health_checker.beat(             type=HealthDataType.EXCEPTION,             data=traceback.format_exc()         )     self._health_checker.beat(         type=HealthDataType.STOPPED,         data='FINISH'     )     self._health_checker.stop()     self._health_checker.join()

Listing 2 – Detected Objects Processing Procedure 
def __handle_predictions(self):      predictions: list[DetectionResult] = self.__get_predictions()     self.__handle_results(predictions)     self.__save_results() 
def __handle_results(self, predictions: list[DetectionResult]):     for res in predictions:          video, video_dt = self.__videos_writer.set_frame(res.cap_image)         self.__eventor.set_data(res.cap_image.meta.source,                                 res.cap_image.meta.dt,                                 video,                                 video_dt,                                 res.predictions)

Listing 3 – Loading Detection
def set_data(
        self,
        source: str,
        src_dt: datetime.datetime,
        video_name: str,
        video_time: datetime.timedelta,
        predictions: list[Prediction]
):
    # If this is a new source and its data has not been initialized, set a default value
    if self.__areas_interest.get(source, None) is None:
        self.add_or_update_interest_area(source, None)
    if not self.__time_without_ladle.get(source, None):
        self.add_or_update_bucket_loss_time(source, self._TIME_WITHOUT_LADlE_DEFAULT)

    predictions = self.get_needed_prediction(predictions)
    is_arrived = (any(
            (
                prediction.name in self.__interest_objs
                and self.__check_area(source, prediction)
            )
            for prediction in predictions
    ))
    value = TractorStates.ARRIVED if is_arrived else TractorStates.DEPARTED

    self.__determine_event(
        source, src_dt, video_name, video_time, value
    )

def __determine_event(
        self,
        source: str,
        src_dt: datetime.datetime,
        video_name: str,
        video_dt: datetime.timedelta,
        state: TractorStates
):
    if not (current_state := self.__states.get(source, None)):
        current_state = State(
            value=state.value,
            dt=src_dt
        )
        self.__states[source] = current_state
        self.__add_new_state(current_state, source, video_name, video_dt)
        return

    if current_state.value == TractorStates.DEPARTED.value:
        # If the current state is "Departed" and the new state is also "Departed"
        if state == TractorStates.DEPARTED:
            # then do not change anything
            return
    else:
        # If the current state is "Arrived" and the new state is also "Arrived"
        if state == TractorStates.ARRIVED:
            # then update the arrival time
            current_state.dt = src_dt
            return

        # If the "Arrived" state has not been updated for less than N time
        if (src_dt - current_state.dt) < self.__time_without_ladle[source]:
            # then do not change the state to "Departed"
            return

    current_state.value = state.value
    current_state.dt = src_dt
    self.__add_new_state(current_state, source, video_name, video_dt)
