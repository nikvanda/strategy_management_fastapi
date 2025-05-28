class BaseStrategyError(Exception):
    pass


class InvalidStrategyField(BaseStrategyError):
    def __init__(self, field: str, message=None, errors=None):
        message = f'Strategy does not have field: {field}'
        super().__init__(message)

        self.errors = errors


class IncorrectStatusTypesError(BaseStrategyError):
    def __init__(self, message='Incorrect status type.', errors=None):
        super().__init__(message)

        self.errors = errors


class StrategyNotExistError(BaseStrategyError):
    def __init__(self, message='Strategy does not exist', errors=None):
        super().__init__(message)

        self.errors = errors


class StrategyCreationError(BaseStrategyError):
    def __init__(self, message=None, strategy_data=None, user_id=None):
        message = f'Can\'t create strategy {strategy_data.name} for user {user_id}'

        super().__init__(message)
        self.strategy_data = strategy_data
        self.user_id = user_id


class BaseConditionError(Exception):
    pass


class IncorrectConditionTypeError(BaseConditionError):
    def __init__(self, message='Incorrect condition types.', errors=None):
        super().__init__(message)

        self.errors = errors


class InvalidConditionData(BaseConditionError):
    def __init__(self, message='Some keys are missed', errors=None):
        super().__init__(message)

        self.errors = errors


class InvalidConditionDataStructureError(BaseConditionError):
    def __init__(self, structure_type: str, message=None, errors=None):
        message = f'Type {structure_type} is not supported.'
        super().__init__(message)

        self.errors = errors

class ConditionFailToCreateError(BaseConditionError):
    def __init__(self, message=None, condition_data=None):
        message = f'Can\'t create condition {condition_data.indicator} - {condition_data.threshold}'
        super().__init__(message)
        self.condition_data = condition_data
