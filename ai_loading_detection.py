class LoadingDetection:
    def run(self) -> None:
        self.__init__()
        self._health_checker.beat(
            type=HealthDataType.DATA,
            data="START"
        )
        try:
            while self._continue_work():
                if self._image_queue.empty():
                    time.sleep(self._sleep_time_attempting_get_task)
                    continue
                cap_image: CapturedImage = self._image_queue.get()
                image = cap_image.get_image()
                predictions = self._net_image_detection(image)
                result = DetectionResult(
                    cap_image=cap_image,
                    predictions=predictions
                )
                self._result_queue.put(result)
        except Exception as ex:
            self._health_checker.beat(
                type=HealthDataType.EXCEPTION,
                data=traceback.format_exc()
            )
        self._health_checker.beat(
            type=HealthDataType.STOPPED,
            data="FINISH"
        )
        self._health_checker.stop()
        self._health_checker.join()

    # Listing 2 – Detected Objects Processing
    def _handle_predictions(self):
        predictions: list[DetectionResult] = self._get_predictions()
        self._handle_results(predictions)
        self._save_results()

    def _handle_results(self, predictions: list[DetectionResult]):
        for res in predictions:
            video, video_dt = self._videos_writer.set_frame(res.cap_image)
            self._eventor.set_data(
                res.cap_image.meta.source,
                res.cap_image.meta.dt,
                video,
                video_dt,
                res.predictions
            )

    # Listing 3 – Loading Detection
    class LoadingEvent:
        def __init__(self):
            self.source: str
            self.src_dt: datetime.datetime
            self.video_name: str
            self.video_time: datetime.timedelta
            self.list_prediction: list[DetectionResult]

# If this is a new source and its data has not been initialized, then we set the value by default
