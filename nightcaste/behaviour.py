import input
import logging
import utils
from components import Direction


class BehaviourManager:
    """The Bahavoiur manager stores component behevoiurs."""
    logger = logging.getLogger('behaviour.BehaviourManager')

    def __init__(self, event_manager, entitiy_manager, config=None):
        self.event_manager = event_manager
        self.entity_manager = entitiy_manager
        self.behaviours = {}
        if config is not None:
            self.configure(config)

    def configure(self, config):
        """Configure behaviourse base on a configuration.

        Ars:
            config: {'component_behaviours': [{component_type, name: ''}]}

        """
        if 'component_behaviours' in config:
            for comp_behaviour_config in config['component_behaviours']:
                self.add_comp_behaviour_from_config(comp_behaviour_config)
        if 'min_turn_time' in config:
            self.min_turn_time = config['min_turn_time']

    def add_comp_behaviour_from_config(self, config):
        """Associates the behaviour specified be the name with the specified
        compoenent_type.

        Args:
            component_type (str): The component type associated with the
                behaviour
            behaviour_impl (str): The implementation of the behaviour.

        """
        impl = config['impl']
        behaviour_class = utils.class_for_name(impl[0], impl[1])
        behaviour = behaviour_class(self.event_manager, self.entity_manager)
        self.add_component_behaviour(config['component_type'], behaviour)

    def add_component_behaviour(self, component_type, behaviour):
        """Register the given behaviour with the specified component type."""
        self.logger.debug("Register %s for component type %s",
                          component_type, behaviour)
        self.behaviours.update({component_type: behaviour})

    def update(self, round, delta_time):
        """Updates all behaviours for all entitites with a associated
        components."""
        for component_type, behaviour in self.behaviours.iteritems():
            components = self.entity_manager.get_all(component_type)
            for entity, component in components.iteritems():
                behaviour.entity = entity
                behaviour.component = component
                behaviour.update(round, delta_time)


class TurnBehaviourManager(BehaviourManager):

    logger = logging.getLogger('behaviour.TurnBehaviourManager')

    def __init__(self, event_manager, entitiy_manager, config=None):
        BehaviourManager.__init__(self, event_manager,
                                  entitiy_manager, config)
        self.locked_entities = []

    def update(self, round, delta_time):
        """Updates all behaviours for all entitites with a associated
        component, but only if there are no locked entities."""

        # TODO: Make the method prettier ^^
        for component_type, behaviour in self.behaviours.iteritems():
            components = self.entity_manager.get_all(component_type)

            for entity, component in components.iteritems():
                s = self.locked_entities
                turn = self.entity_manager.get(entity, "Turn")
                if (turn.ticks == 0 and turn.delta >= turn.min_turn_time):
                    # It's the entity's Turn!
                    if (turn.locking and entity not in s):
                        # Lock it
                        self.locked_entities.append(entity)
                    if (entity in s or len(s) == 0):
                        behaviour.entity = entity
                        behaviour.component = component
                        ticks = behaviour.update(round, delta_time)
                        if (ticks is not None):
                            # The behaviour has made an action
                            if (entity in s):
                                self.locked_entities.remove(entity)
                            self._add_ticks(entity, ticks)
                else:
                    turn.delta += delta_time
        self._normalize()

    def _add_ticks(self, entity, ticks):
        """ Count up the Tick Counter of entity, and reset its delta time """
        turn_comp = self.entity_manager.get(entity, "Turn")
        turn_comp.ticks += ticks
        turn_comp.delta = 0

    def _normalize(self):
        """ Reduce the Tick counter of all turn components by the minimum
        Tick count, to prevent tick counters from increasing indefinitely.
        This assures an only relative tick count """
        min_ticks = None
        for component_type, behaviour in self.behaviours.iteritems():
            components = self.entity_manager.get_all(component_type)
            ticks = [self.entity_manager.get(entity, "Turn").ticks
                     for entity in components.keys()]
            if (len(ticks) > 0):
                minimum_of_type = min(ticks)
                if (min_ticks is None or min_ticks > minimum_of_type):
                    min_ticks = minimum_of_type
        if min_ticks is not None:
            for component_type, behaviour in self.behaviours.iteritems():
                components = self.entity_manager.get_all(component_type)
                for turn_comp in [self.entity_manager.get(entity, "Turn")
                                  for entity in components.keys()]:
                    turn_comp.ticks -= min_ticks


class EntityComponentBehaviour(object):
    """Implements logic for entities with specific components."""

    def __init__(self, event_manager, entitiy_manager):
        self.entity_manager = entitiy_manager
        self.event_manager = event_manager
        self.entity = None
        self.component = None

    def update(self, round, delta_time):
        pass


class InputBehaviour(EntityComponentBehaviour):
    """Implements User Input. Controls all entites with an InputComponent."""

    logger = logging.getLogger('behaviours.InputBehaviour')

    def __init__(self, event_manager, entitiy_manager):
        super(InputBehaviour, self).__init__(event_manager, entitiy_manager)
        # TODO make configurable
        self.isometric = True

    def update(self, round, delta_time):
        """Converts input to an appropriate InputAction."""
        # TODO Implement gamestatus aware behaviour manager to keep the turn
        # based logic as central as possible and possibly enable switching
        # between realtime and turn based. (A realtime behaviour would not
        # check for a state
        speed = self.move()

        if input.is_pressed(input.K_ENTER):
            # TODO: Implement Targeting Inputs (combined input or
            # sequential?)
            # TODISCUSS: Context actions, autotargeting
            speed = self.use(0, 0)
        return speed

    def set_input_direction(self):
        direction = self.component.direction
        if input.is_pressed(
            input.K_LEFT) or input.is_pressed(
            input.K_KP1) or input.is_pressed(
            input.K_KP4) or input.is_pressed(
                input.K_KP7):
            direction.set(Direction.D_LEFT)
        else:
            direction.set(Direction.D_LEFT, 0)
        if input.is_pressed(
            input.K_RIGHT) or input.is_pressed(
            input.K_KP3) or input.is_pressed(
            input.K_KP6) or input.is_pressed(
                input.K_KP9):
            direction.set(Direction.D_RIGHT)
        else:
            direction.set(Direction.D_RIGHT, 0)
        if input.is_pressed(
            input.K_DOWN) or input.is_pressed(
            input.K_KP1) or input.is_pressed(
            input.K_KP2) or input.is_pressed(
                input.K_KP3):
            direction.set(Direction.D_DOWN)
        else:
            direction.set(Direction.D_DOWN, 0)
        if input.is_pressed(
            input.K_UP) or input.is_pressed(
            input.K_KP7) or input.is_pressed(
            input.K_KP8) or input.is_pressed(
                input.K_KP9):
            direction.set(Direction.D_UP)
        else:
            direction.set(Direction.D_UP, 0)

    def set_iso_input_direction(self):
        direction = self.component.direction
        if input.is_pressed(
            input.K_LEFT) or input.is_pressed(
            input.K_UP) or input.is_pressed(
            input.K_KP4) or input.is_pressed(
            input.K_KP7) or input.is_pressed(
                input.K_KP8):
            direction.set(Direction.D_LEFT)
        else:
            direction.set(Direction.D_LEFT, 0)
        if input.is_pressed(
            input.K_RIGHT) or input.is_pressed(
            input.K_DOWN) or input.is_pressed(
            input.K_KP2) or input.is_pressed(
            input.K_KP3) or input.is_pressed(
                input.K_KP6):
            direction.set(Direction.D_RIGHT)
        else:
            direction.set(Direction.D_RIGHT, 0)
        if input.is_pressed(
            input.K_LEFT) or input.is_pressed(
            input.K_DOWN) or input.is_pressed(
            input.K_KP4) or input.is_pressed(
            input.K_KP1) or input.is_pressed(
                input.K_KP2):
            direction.set(Direction.D_DOWN)
        else:
            direction.set(Direction.D_DOWN, 0)
        if input.is_pressed(
            input.K_RIGHT) or input.is_pressed(
            input.K_UP) or input.is_pressed(
            input.K_KP6) or input.is_pressed(
            input.K_KP8) or input.is_pressed(
                input.K_KP9):
            direction.set(Direction.D_UP)
        else:
            direction.set(Direction.D_UP, 0)


    def move(self):
        """Throws a MoveAction."""
        if self.isometric:
            self.set_iso_input_direction()
        else:
            self.set_input_direction()
        return 1 if self.component.direction.direction > 0 else None

    def use(self, dx, dy):
        """ Throws a UseEntity Event """
        self.event_manager.throw("UseEntityAction", {
            'user': self.entity})
        return 2
