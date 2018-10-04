"""
Code based on https://github.com/flywheel-io/bids-client/blob/084e19c027970ed33338279174034a7839b6f359/flywheel_bids/upload_bids.py#L142
and extended to control project creation in more detail
"""
import logging

logger = logging.getLogger("dynagefw")


def handle_project(fw, project_label, group_id, create=False, raise_on=None):
    """ Returns a Flywheel project based on group_id and project_label
    If project exists, project will be retrieved,
     else project will be created

     FL: parts about disabling acquisition rules were removed since we don't work with acquisitions
    """

    if raise_on not in [None, "missing", "existing"]:
        raise Exception("raise_on value not valid {}".format(raise_on))

    # Get all projects
    existing_projs = fw.get_all_projects()
    # Determine if project_label with group_id already exists
    found = False
    for ep in existing_projs:
        if (ep['label'] == project_label) and (ep['group'] == group_id):
            logger.info('Project (%s) was found. Adding data to existing project.' % project_label)
            # project exists
            project = ep
            found = True
            break

    if found and raise_on == "existing":
        raise Exception("Project {} found but raise_on='existing'".format(project_label))

    if not found and raise_on == "missing":
        raise Exception("Project {} not found but raise_on='missing'".format(project_label))

    if not found and not create:
        raise Exception("There is no project {} and you don't want to create one. This doesn't make sense.".format(
            project_label))

    # If project does not exist, create project
    if not found and create:
        if not group_id:
            raise Exception("A project {} is going to be created, but you did not provide group_id".format(
                project_label))
        logger.info('Project (%s) not found. Creating new project for group %s.' % (project_label, group_id))
        project_id = fw.add_project({'label': project_label, 'group': group_id})
        project = fw.get_project(project_id)

    return project.to_dict()


def get_subject_session(fw, project_id, subject_name):
    """ Returns a Flywheel session based on project_id and session_label
    If session exists, session will be retrieved,
     else session will be created
    """
    # Get all sessions
    existing_sessions = fw.get_project_sessions(project_id)
    # Determine if session_name within project project_id already exists, with same subject_name...

    for es in existing_sessions:
        if es['subject']['code'] == subject_name:
            logger.info('Subject {} was found. Adding data to existing session.'.format(subject_name))
            # Session exists
            session = es
            return session.to_dict()

