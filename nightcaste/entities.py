"""The model represents backing storage for entities."""
import components
import json
import logging
import os

logger = logging.getLogger('entites')


class EntityManager:
    """The EntityManager is the interface for all systems to create and retrieve
    entites e.g their components"""

    def __init__(self):
        self.last_id = -1
        self.component_manager = ComponentManager()
        self.blueprint_manager = BlueprintManager()
        self.current_map = None
        self.player = None

        # TODO: Pass path from engine? Or pass someting similar like
        # EntityConfiguration but more general
        BP_DIR = os.path.abspath(
            os.path.join(
                os.path.dirname(__file__),
                '..',
                'config',
                'blueprints'))
        self.blueprint_manager.initialize(BP_DIR)

    def create_entity(self):
        """Creates a new empty entity woth no components associated.

            Returns:
                The new entity identifier.

        """
        self.last_id += 1
        return self.last_id

    def new_from_config(self, configuration):
        """Constructs a new entity with the components and properties specified
        in the configuration.

            Args:
                configuration (EntityConfiguration): The configuration from
                    which the components are constructed.

            Returns:
                The new entity identifier.

        """
        entity = self.create_entity()
        self.component_manager.add_components(entity, configuration)
        return entity

    def new_from_blueprint(self, blueprint):
        """Constructs a new entity by creating a configuration from a blueprint.

            Args:
                blueprint (str): The name of the blueprint.

            Returns:
                The new entity identifier.

        """
        configuration = self.blueprint_manager.get_entity_configuration(
            blueprint)
        return self.new_from_config(configuration)

    def new_from_blueprint_and_config(self, blueprint, entity_config):
        """Constructs a new entity by creating a configuration from a blueprint
        and updates it attributes with the given config.

            Args:
                blueprint (str): The name of the blueprint.
                entity_config (EntityConfiguration): Config to update the
                    template with

            Returns:
                The new entity identifier.

        """
        blueprint_config = self.blueprint_manager.get_entity_configuration(
            blueprint)
        blueprint_config.update(entity_config)
        return self.new_from_config(blueprint_config)

    def destroy_entity(self, entity):
        """Removes all components which belong to the given entity.

            Args:
                entity (object): The entity to destroy.

        """
        self.component_manager.remove_components(entity)

    def get(self, entity, component_type):
        """Searches the specified component type for the given entity.

            Args:
                entity (object): The entity identifier.
                component_type (str): The component type to search for.

            Returns:
                The specified entity component or None in case the component
                could not be found.

        """
        return self.component_manager.get_component(entity, component_type)

    def set_entity_attribute(self, entity_id, component, attribute, value):
        """ Set an attribute of component of entity """

        component = self.get(entity_id, component)
        if component is not None:
            component.attribute = value

    def get_all_of_type(self, component_type):
        """Get all components of the specified type.

            Args:
                component_type (str): The component type to retrieve.

            Returns:
                A dictionary in the form of {entity: component}.

        """
        return self.component_manager.get_all_of_type(component_type)

    def get_components_for_entities(self, entity_list, component_type):
        """Get the components of the specified type and for the specified entity
        list.

            Args:
                entity_list: List or dictionary containing entity identifiers.
                component_type (str): The component type to return.

            Returns:
                A dictionary in the form of {entity: component}.

        """
        out = dict()
        for entity in entity_list:
            out[entity] = self.get(entity, component_type)
        return out

    def get_current_map(self):
        """ Returns the tiles array of the current map """
        return self.get(self.current_map, "Map").tiles


class ComponentManager:
    """ The Component manager stores the components for all entities, which are
    only represented through an internal entitiy identifier."""

    def __init__(self):
        # Two-dimensional dictionary holding the components of all entities
        # {component_type: {entity_id: Component}}
        self.components = {}

    def add_component(self, entity_id, component):
        """Adds the specified component for the given entity the the component
        database."""
        component_type = component.type()
        component_dict = self.components.get(component_type)
        if (component_dict is None):
            component_dict = {}
            self.components[component_type] = component_dict
        component_dict[entity_id] = component

    def add_components(self, entity_id, configuration):
        """Create and add components based on the given configuration."""
        for component_name, attributes in configuration.components.iteritems():
            component = getattr(components, component_name)()

            "Add all attributes to component"
            for attr_name, attr_value in attributes.iteritems():
                setattr(component, attr_name, attr_value)

            self.add_component(entity_id, component)

    def remove_component(self, entity_id, component_type):
        """Removes a specific entity component from the component database.

            Args:
                entity_id (long): The entity from which the component should be
                    removed.
                component_type (str): The the type of component to remove.

            Returns:
                The component which was removed or None if the component_type or
                entity does not exists.

        """
        component_entities = self.components.get(component_type)
        if component_entities is None:
            return None
        return component_entities.pop(entity_id, None)

    def remove_components(self, entity_id):
        """Calls remove component with the specified entity_id for each known
        component type"""
        for component_type in self.components:
            self.remove_component(entity_id, component_type)

    def get_component(self, entity_id, component_type):
        """Get an entity component.

            Returns:
                The component or None if the component does not exists

        """
        component_dict = self.components.get(component_type)
        if component_dict is None:
            return None
        return component_dict.get(entity_id)

    def get_all_of_type(self, component_type):
        """Get all components of the given type

            Returns:
                A dictionary containing all components of component_type
                or an empty dictionary, if none exist

        """
        component_dict = self.components.get(component_type)
        if component_dict is None:
            component_dict = {}
        return component_dict


class BlueprintManager:
    """Stores blueprints which can be used as templates for entity creation. The
    blueprints are stored on disk in JSON format."""

    def __init__(self):
        self.blue_prints = {}

    def get_entity_configuration(self, blueprint):
        """Get the entity configuration for the specified blueprint
        """
        return self.blue_prints.get(blueprint)

    def initialize(self, blueprint_base_path):
        """Loads all blueprints from the specified directory (not recursive).
        The blueprint name is constructed as file.json_object. For example a
        file named tiles.json with { stone_wall: {}} results in the name
        tiles.stone_wall.

        Args:
            blueprint_base_path (str): Path to a directory containing the
                blueprint files.

        """
        logger.info('Initializing Blueprints from: %s', blueprint_base_path)
        for f in os.listdir(blueprint_base_path):
            blueprint_path = os.path.join(blueprint_base_path, f)
            if os.path.isfile(blueprint_path):
                self._load_blueprints_from_file(blueprint_path)

    def _load_blueprints_from_file(self, blueprint_path):
        basename = os.path.splitext(os.path.basename(blueprint_path))[0]
        logger.info('Loading %s', basename)
        blueprint_config = self._load_json(blueprint_path)
        for name, blueprint in blueprint_config.iteritems():
            logger.info("Adding Blueprint: %s", name)
            blue_print_name = basename + '.' + name
            entity_config = self._create_entity_config(blueprint)
            self.blue_prints.update({blue_print_name: entity_config})

    def _load_json(self, path):
        json_file = open(path)
        try:
            return json.load(json_file, 'utf-8')
        finally:
            json_file.close()

    def _create_entity_config(self, blueprint):
        entity_config = EntityConfiguration()
        for component in blueprint['components']:
            logger.debug('Adding blueprint component %s', component)
            entity_config.add_component(component)
        self._configure_entity_attributes(blueprint, entity_config)
        return entity_config

    def _configure_entity_attributes(self, blueprint, entity_config):
        for attribute, value in blueprint['attributes'].iteritems():
            component_attribute = attribute.split('.')
            entity_config.add_attribute(
                component_attribute[0], component_attribute[1], value)


class EntityConfiguration:
    """Stores the necessary information the construct an entity

        TODO:
            - Select better data structure than nested dictionaries
              => may be a combined key 'Position.x': value
              => Complete object structure: Component with a List of Attributes
                 an Attribute is a key value pair
            - Provide easy acceess to all information
            - Mimic Json Structure so an configuration and a blueprint can be
              trated analog
            - Make a mor general configuration object to configure processors
              and systems with a configuration (which can be stored on disk^^)

    """

    def __init__(self):
        self.components = {}

    def __str__(self):
        return str(self.components)

    def add_component(self, component):
        if component not in self.components:
            self.components.update({component: {}})

    def add_attribute(self, component, name, value):
        """Add an attribute for the specified component

            TODO: May select better structure than dictionaries"""
        if component not in self.components:
            self.components.update({component: {name: value}})
        else:
            component_attributes = self.components[component]
            component_attributes.update({name: value})

    def get_attributes(self, component):
        if component not in self.components:
            return {}

        return self.components[component]

    def update(self, other):
        """Adds components and attributes from the given configuration to this
        configuration. Existing attribute values are replaced."""
        for other_component, attributes in other.components.iteritems():
            if len(attributes) == 0 and other_component not in self.components:
                self.add_component(other_component)
            else:
                for name, value in attributes.iteritems():
                    self.add_attribute(other_component, name, value)
