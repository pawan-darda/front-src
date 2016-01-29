'''
Created on 9 march 2011

@author: pawan.darda
'''
from django.conf.urls.defaults import patterns

urlpatterns = patterns('DjangoWebSite.portlets.views',
    (r'^build_sprs','build_sprs'),
    (r'^perf_graph','perf_graph'),
    (r'^graph_data','graph_data'),
    (r'^create_wall','create_wall'),
    (r'^add_portlet', 'add_portlet'),
    (r'^delete_portlet', 'delete_portlet'),
    (r'^edit_portlet', 'edit_portlet'),
    (r'^update_postion', 'update_postion'),
    (r'^asg_scenario', 'asg_scenario'),
    (r'^get_nice_name', 'get_nice_name'),
    (r'^get_branch_name', 'get_branch_name'),
    (r'^get_pg_scenario', 'get_pg_scenario'),
    (r'^get_pg_column', 'get_pg_column'),
    (r'^get_pg_label', 'get_pg_label'),
    (r'^find_wall', 'find_wall'),
    (r'^delete_wall', 'delete_wall'),
    (r'^scenario_unittest', 'scenario_unittest'),
    (r'^build_status', 'build_status'),
    (r'^get_unittest_versions', 'get_unittest_versions'),
    (r'^get_bs_nicename', 'get_bs_nicename'),
    (r'^get_bs_componentgroup', 'get_bs_componentgroup'),
    (r'^edit_wall', 'edit_wall'),
    (r'^unittest_grid_widget', 'unittest_grid_widget')
    )

