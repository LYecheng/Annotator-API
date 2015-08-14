<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN"
        "http://www.w3.org/TR/html4/loose.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">

<head>
  <meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
</head>

<body>
  <h1>Annotate VCF File</h1>

  <form id="upload_form" action="https://{{bucket_name}}.s3.amazonaws.com/" method="post" enctype="multipart/form-data">
    <!-- Include required AWS S3 parameters as hidden fields here -->
    <!-- An example, the AWS Access Key is shown below -->
    
    <input type="hidden"  name="key" value="lyc/{{job_id}}~${filename}" /><br />
    <input type="hidden" name="AWSAccessKeyId" value="{{aws_key}}">
    <input type="hidden" name="acl" value="{{acl}}" />
    <input type="hidden" name="success_action_redirect" value="http://lyc.ucmpcs.org:8888/redirect" /> 
    <input type="hidden"   name="X-Amz-Algorithm" value="{{algorithm}}" />
    <input type="hidden" name="Policy" value='{{encoded_policy}}' />
    <input type="hidden" name="Signature" value="{{signature}}" />

    <br>VCF Input File: <input id="upload_file" type="file" name="file" /><br>

    <br><input type="submit" value="Run Annotator" /></br>

    <br><a href="/list">View list of files in directory /lyc</a><br>

  </form>

</body>
</html>