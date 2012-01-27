<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN"
    "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en" lang="en">
<head>
  <meta http-equiv="Content-Type" content="text/html;charset=utf-8" />
  <title>Foresight - {{title}}</title>
  <!-- 
  <link type="text/css" rel="stylesheet" media="all" href="/static/site.css" />
  -->
  <link rel="stylesheet" href="/static/bootstrap.min.css">
  <link rel="shortcut icon" href="/static/img/favicon.ico" type="image/x-icon"/>

  <style type="text/css">
      /* Override some defaults */
      html, body {
        background-color: #eee;
      }
      body {
        padding-top: 40px; /* 40px to make the container go all the way to the bottom of the topbar */
      }
      .container > footer p {
        text-align: center; /* center align it with the container */
      }
      .container {
        width: 820px; /* downsize our container to make the content feel a bit tighter and more cohesive. NOTE: this removes two full columns from the grid, meaning you only go to 14 columns and not 16. */
      }

      /* The white background content wrapper */
      .content {
        background-color: #fff;
        padding: 20px;
        margin: 0 -20px; /* negative indent the amount of the padding to maintain the grid system */
        -webkit-border-radius: 0 0 6px 6px;
           -moz-border-radius: 0 0 6px 6px;
                border-radius: 0 0 6px 6px;
        -webkit-box-shadow: 0 1px 2px rgba(0,0,0,.15);
           -moz-box-shadow: 0 1px 2px rgba(0,0,0,.15);
                box-shadow: 0 1px 2px rgba(0,0,0,.15);
      }

      /* Page header tweaks */
      .page-header {
        background-color: #f5f5f5;
        padding: 20px 20px 10px;
        margin: -20px -20px 20px;
      }

      /* Styles you shouldn't keep as they are for displaying this base example only */
      .content .span10,
      .content .span4 {
        min-height: 500px;
      }
      /* Give a quick and non-cross-browser friendly divider */
      .content .span4 {
        margin-left: 0;
        padding-left: 19px;
        border-left: 1px solid #eee;
      }

      .topbar .btn {
        border: 0;
      }

    </style>

</head>
<body>
  <div class="topbar" id="navbar">
	<div class="fill">
	<div class="container">
	      <a class="brand" id="current" href="/">Foresight Linux Packages</a>
	    <ul class="nav">
	      <li class="active"><a href="http://www.foresightlinux.org">Foresight Linux Site</a></li>
	      <li><a href="http://forum.foresightlinux.org">Forum</a></li>
	      <li><a href="http://issues.foresightlinux.org" title="Foresight Issue Tracking System">FITS</a></li>
	    </ul>
	</div>
	</div>
  </div>
  <div id="content" class="container">
	<div class="content">
    %include
	</div>
<footer>
<p>  Any issue with this website, please report to
  <a href="https://github.com/zhangsen/fl-pkgs-web">the github page</a>.
</p>
</footer>
  </div>
</body>
</html>
