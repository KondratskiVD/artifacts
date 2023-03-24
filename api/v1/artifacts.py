from flask import request

from hurry.filesize import size

from flask_restful import Resource

from tools import MinioClient, api_tools, MinioClientAdmin
from pylon.core.tools import log


def calculate_readable_retention_policy(days: int) -> dict:
    if days and days % 365 == 0:
        expiration_measure, expiration_value = 'years', days // 365
    elif days and days % 31 == 0:
        expiration_measure, expiration_value = 'months', days // 31
    elif days and days % 7 == 0:
        expiration_measure, expiration_value = 'weeks', days // 7
    else:
        expiration_measure, expiration_value = 'days', days
    return {
        'expiration_measure': expiration_measure,
        'expiration_value': expiration_value
    }


class ProjectAPI(api_tools.APIModeHandler):

    def get(self, project_id: int, bucket: str):
        project = self.module.context.rpc_manager.call.project_get_or_404(project_id=project_id)
        c = MinioClient(project)
        try:
            lifecycle = c.get_bucket_lifecycle(bucket)
            retention_policy = calculate_readable_retention_policy(
                days=lifecycle["Rules"][0]['Expiration']['Days']
                )
        except Exception:
            retention_policy = None
        files = c.list_files(bucket)
        for each in files:
            each["size"] = size(each["size"])
        return {"retention_policy": retention_policy, "total": len(files), "rows": files}

    def post(self, project_id: int, bucket: str):
        project = self.module.context.rpc_manager.call.project_get_or_404(project_id=project_id)
        c = MinioClient(project=project)
        if "file" in request.files:
            api_tools.upload_file(bucket, request.files["file"], project)
        return {"message": "Done", "size": size(c.get_bucket_size(bucket))}, 200

    def delete(self, project_id: int, bucket: str):
        args = request.args
        project = self.module.context.rpc_manager.call.project_get_or_404(project_id=project_id)
        c = MinioClient(project=project)
        if not args.get("fname[]"):
            c.remove_bucket(bucket)
        else:
            for fname in args.getlist("fname[]"):
                c.remove_file(bucket, fname)
        return {"message": "Deleted", "size": size(c.get_bucket_size(bucket))}, 200


class AdminAPI(api_tools.APIModeHandler):
    def get(self, project_id: int, bucket: str):
        c = MinioClientAdmin()
        try:
            lifecycle = c.get_bucket_lifecycle(bucket)
            retention_policy = calculate_readable_retention_policy(
                days=lifecycle["Rules"][0]['Expiration']['Days']
            )
        except Exception:
            retention_policy = None
        files = c.list_files(bucket)
        for each in files:
            each["size"] = size(each["size"])
        return {"retention_policy": retention_policy, "total": len(files), "rows": files}

    def post(self, project_id: int, bucket: str):
        c = MinioClientAdmin()
        if "file" in request.files:
            api_tools.upload_file_admin(bucket, request.files["file"])
        return {"message": "Done", "size": size(c.get_bucket_size(bucket))}, 200

    def delete(self, project_id: int, bucket: str):
        args = request.args
        c = MinioClientAdmin()
        if not args.get("fname[]"):
            c.remove_bucket(bucket)
        else:
            for fname in args.getlist("fname[]"):
                c.remove_file(bucket, fname)
        return {"message": "Deleted", "size": size(c.get_bucket_size(bucket))}, 200


class API(api_tools.APIBase):
    url_params = [
        '<string:mode>/<int:project_id>/<string:bucket>',
        '<int:project_id>/<string:bucket>',
    ]

    mode_handlers = {
        'default': ProjectAPI,
        'administration': AdminAPI
    }
