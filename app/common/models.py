from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    def __str__(self):
        return (
            f"{self.__class__.__name__} - ("
            + str(
                dict(
                    zip(
                        self.__class__.__table__.columns.keys(),
                        [
                            self.__dict__.get(item)
                            for item in self.__class__.__table__.columns.keys()
                        ],
                        strict=True,
                    )
                )
            )
            + ")"
        )

    def __repr__(self):
        return str(self)

    def copy(self, **overrides):
        data = {
            c.key: getattr(self, c.key)
            for c in self.__table__.columns
            if c.key not in overrides
        }
        data.update(overrides)
        return self.__class__(**data)
