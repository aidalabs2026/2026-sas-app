from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.date import DateTrigger
from datetime import datetime, timedelta
import time

class ApplyScheduler:
    def __init__(self, connected_clients):
        self.scheduler = BackgroundScheduler()
        self.scheduler.start()
        self.jobs = {}
        self.connected_clients = connected_clients



    def add_non_periodic_event(self, apply_id, non_periodic_id, start_date, end_date,
                  start_func=None, end_func=None):
        """
        event_id        : 이벤트 식별자
        start_date      : 시작일 (datetime)
        end_date        : 만료일 (datetime)
        start_func      : 시작일에 실행할 함수
        end_func        : 만료일에 실행할 함수
        """

        # 시작일 함수
        if start_func:
            try:
                job = self.scheduler.add_job(
                    start_func, 'date',
                    run_date=start_date,
                    args=[apply_id],
                    id=f"{apply_id}_{non_periodic_id}_start"
                )
                self.jobs[f"{apply_id}_{non_periodic_id}_start"] = job
                print(f"[INFO] start_func job 등록 완료: {job.id}, 실행 예정 시각={start_date}")
            except Exception as e:
                print(f"[ERROR] start_func job 추가 실패: {e}")

        # 만료일 함수
        if end_func:
            try:
                job = self.scheduler.add_job(
                    end_func, 'date',
                    run_date=end_date,
                    args=[apply_id],
                    id=f"{apply_id}_{non_periodic_id}_end"
                )
                self.jobs[f"{apply_id}_{non_periodic_id}_end"] = job
                print(f"[INFO] end_func job 등록 완료: {job.id}, 실행 예정 시각={end_date}")
            except Exception as e:
                print(f"[ERROR] end_func job 추가 실패: {e}")

    def _parse_time_arg(t):
        """
        문자열 'HH:MM', datetime.time, datetime.timedelta 모두 처리 가능.
        반환값: (hour, minute)
        """
        if t is None:
            return 0, 0
        if isinstance(t, str):
            h, m = map(int, t.split(":"))
            return h, m
        elif isinstance(t, time):
            return t.hour, t.minute
        elif isinstance(t, timedelta):
            total_seconds = int(t.total_seconds())
            hours = total_seconds // 3600
            minutes = (total_seconds % 3600) // 60
            return hours, minutes
        else:
            raise TypeError(f"Unsupported time format: {type(t)}")

    def add_periodic_event(self, event_id, start_date, expire_date, repeat_days, day_start_time, day_end_time,  on_day_start=None, on_day_end=None):
        """
        :param event_id: 이벤트 식별자
        :param start_date: datetime, 전체 주기의 시작일
        :param expire_date: datetime, 전체 주기의 만료일
        :param repeat_days: list, 실행 요일 ex) ["mon", "wed", "fri"]
        """
        """
        # 주기 시작 알림
        self.scheduler.add_job(
            func=self.on_period_start,
            trigger=DateTrigger(run_date=start_date),
            args=[event_id],
            id=f"{event_id}_period_start"
        )

        # 주기 종료 알림
        self.scheduler.add_job(
            func=self.on_period_end,
            trigger=DateTrigger(run_date=expire_date),
            args=[event_id],
            id=f"{event_id}_period_end"
        )
        """
        # 시간 문자열을 분리
        day_start_time = str(day_start_time)
        start_hour = day_start_time.split(":")[0]
        start_minute = day_start_time.split(":")[1]
        day_end_time = str(day_end_time)
        end_hour = day_end_time.split(":")[0]
        end_minute = day_end_time.split(":")[1]

        # 요일별 실행 (start_date ~ expire_date 사이에서만 동작하도록 end_date 제한)
        # 시작일 요일별 실행
        if on_day_start:
            try:
                job_start = self.scheduler.add_job(
                    func=on_day_start,
                    trigger=CronTrigger(day_of_week=",".join([repeat_days]), hour=start_hour, minute=start_minute, start_date=start_date,
                                        end_date=expire_date),
                    args=[event_id],
                    id=f"{event_id}_day_start"
                )
                self.jobs[f"{event_id}_day_start"] = job_start
                print(f"[INFO] on_day_start job 등록 완료: {job_start.id}, 요일={repeat_days},  시간={day_start_time}, 기간={start_date}~{expire_date}")


            except Exception as e:
                print(f"[ERROR] on_day_start job 등록 실패: {e}")

        # 종료일 요일별 실행
        if on_day_end:
            try:
                job_end = self.scheduler.add_job(
                    func=on_day_end,
                    trigger=CronTrigger(day_of_week=",".join([repeat_days]), hour=end_hour, minute=end_minute, start_date=start_date,
                                        end_date=expire_date),
                    args=[event_id],
                    id=f"{event_id}_day_end"
                )
                self.jobs[f"{event_id}_day_end"] = job_end
                print(f"[INFO] on_day_end job 등록 완료: {job_end.id}, 요일={repeat_days}, 시간={day_end_time}, 기간={start_date}~{expire_date}")


            except Exception as e:
                print(f"[ERROR] on_day_end job 등록 실패: {e}")

    def remove_event(self, apply_id):
        """이벤트 전체(job_start, job_repeat, job_end)를 제거"""
        """
        for suffix in ['start', 'repeat', 'end', '_day_start', '_day_end']:
            job_id = f"{apply_id}_{suffix}"
            job = self.jobs.pop(job_id, None)
            if job:
                self.scheduler.remove_job(job.id)
        """
        jobs_to_remove = [
            job for job in self.scheduler.get_jobs()
            if job.id.startswith(f"{apply_id}_")
        ]
        for job in jobs_to_remove:
            self.scheduler.remove_job(job.id)
            self.jobs.pop(job.id, None)  # self.jobs dict 관리도 같이 제거

    def list_jobs(self):
        """현재 등록된 전체 Job 목록 반환"""
        jobs = self.scheduler.get_jobs()
        result = []
        for job in jobs:
            result.append({
                "id": job.id,
                "next_run_time": str(job.next_run_time),
                "func": str(job.func.__name__)
            })
        return result

    def shutdown(self):
        self.scheduler.shutdown()

    def test_func(self, apply_id):
        print(f"Job for {apply_id} ran successfully at {datetime.now()}")


if __name__ == "__main__":
    scheduler_instance = ApplyScheduler()
    # Add a job for testing, e.g., to run in 10 seconds
    from datetime import datetime, timedelta


    def test_func(apply_id):
        print(f"Job for {apply_id} ran successfully at {datetime.now()}")


    test_date = datetime.now() + timedelta(seconds=10)
    scheduler_instance.add_non_periodic_event(
        apply_id="test_apply_id",
        non_periodic_id="1",
        start_date='2025-09-09 15:54:37',
        end_date='2025-09-09 15:54:37',  # Dummy end date
        start_func=test_func
    )

    print("Scheduler started. Waiting for job to run...", datetime.now())
    try:
        # Keep the main thread alive to allow the scheduler to run
        while True:
            time.sleep(1)
    except (KeyboardInterrupt, SystemExit):
        scheduler_instance.shutdown()
        print("Scheduler shut down gracefully.")