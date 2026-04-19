1. `create-db-and-tables()`:
    * `async with engine.begin() as conn`:
        1. opens a database connection
        2. starts a transaction 
        3. wraps it in an asaync context manager
        gets the connection from the pool, begins the transaction and gives you conn. then commit/ rollbakc when done 
    
    * `SQLModel.metadata.create_all` is sync not async so we use `await conn.run_sync()` to act as a bridge between the async and sync.
        1. sqlalchemy grapbs the underlying synchronous connection.
        2. run the function `create_all` 
        3. returns control back to async  
        4. `SQLModel.metadata` contains the models, fo each model convert to SQL and check if not exists create and if no skip. then execute them on the database.
            `CONCLUSION`: open a connection , tmp switch to sync mode , build tables , switch back, commit and close the connection.

2. `AsyncSessionMaker`:
    1. `bind=engine` connects the session to the database engine, it handles the connection with the database
    2. `class_=AsyncSession` create asynnc sessions, not sync ones , so instead of using basic database commands we use `await and yield`
    3. `expire_on_commit=False` after commit , SQLalchemy expires all the objects, clearing them from the memory, so setting it as false will help use use the objects after they are committed (EX: printing an object after committing it)
    4. `session = AsyncSessionMaker()`:
        * pulls a connection from the engine pool
        * tracks objects and changes made 
        * on commit generates the SQL , sends it to DB and finalize the transaction ( short lived per request )

3. `get_db()` (run code before yield is setup and after is cleanup)
    * creates a new session ( no DB connection yet (lazy))
    * enters the contextmanager, session is ready and the connection will open on first queery,
    * on yield it pauses the function. injects the session into the route and the route runs and uses it 
    * `async with AsyncSessionMaker() as session:`, session it automatically closed, connection returned to the pool and cleanup is done 
        `CONCLUSION:` 
        * one session per request ( avoid data leaks and concurrency issues)
        * automatic cleanup of session
        """
        async def get_db() -> AsyncSession:
            async with AsyncSessionMaker() as session:
                yield session
        """
        # `safer Function`
        """
        async def get_db() -> AsyncSession:
            async with AsyncSessionMaker() as session:
                try:
                    yield session
                except Exception:
                    await session.rollback()
                    raise
                finally:
                    await session.close()
        """
        * ensures rollbacks on errors and cleaner close

4. db queries:
    1.  """
        select(func.count(Appointment.id))
        .where(Appointment.doctor_id == current_doctor.id)
        .where(Appointment.appointment_date == today)
        """
      * count how many appointments for this doctor AND scheduled today same as `(SELECT COUNT(id) FROM appointment WHERE doctor_id = ? AND appointment_date = '2026-04-19';)`

    2. """
        select(Appointment).options(joinedload(Appointment.patient))
        .where(Appointment.doctor_id == current_doctor.id)
        .where(Appointment.appointment_date == today)
        .order_by(Appointment.appointment_time.asc())
        """  
        * joinedload allows to load a related table in the same query
        * if we used select(Appointment) without joinedload then it will load the appointments first and then for each appointment make query to fetch the patient
        * using the joinload it uses a LEFT JOIN 
        `(SELECT *FROM appointment LEFT JOIN patient ON appointment.patient_id = patient.id)`
        * therefore makes it easy to fetch from a related table make using a relationship without extra wuery usage by the system.

    



