1. `display_id: int = Field(default=None, sa_column_kwargs={"autoincrement": True}, index=True, unique=True)`
    * `None` is being sent for the display id due to the Sqlite behaviour regarding non PK coluns 
    * it is set as not null but it is not the PK (UUID is ), therefore SQLite doesnt autommatically fill in the next nuber unless configured to or provide the number itself.
    * therefore using the SQLalchemy sa_column to be explicit 
    * or manually calculate it in the `create_user` function
    """
    result = await db.execute(select(func.max(User.display_id)))
    max_id = result.scalar() or 0
    """
    `Then in the new user object`
    """
    display_id=max_id + 1
    """"


